import { ApiError, getStoredToken, getWebSocketUrl, getString, isObject, request } from './client'
import { apiEndpoints } from './endpoints'
import type { ChatAttachment, ChatDetail, ChatMessage, ChatSummary, SendMessageResult } from './types'

let sharedSocket: WebSocket | null = null
let socketConnectingPromise: Promise<WebSocket> | null = null

interface PendingChatRequest {
  resolve: (res: SendMessageResult) => void
  reject: (err: unknown) => void
  onStatus?: (status: string) => void
}

let activeRequest: PendingChatRequest | null = null

function getOrConnectChatSocket(): Promise<WebSocket> {
  const token = getStoredToken()
  if (!token) {
    return Promise.reject(new ApiError('You must be signed in to send messages.', 401))
  }

  if (sharedSocket && sharedSocket.readyState === WebSocket.OPEN) {
    return Promise.resolve(sharedSocket)
  }

  if (socketConnectingPromise) {
    return socketConnectingPromise
  }

  socketConnectingPromise = new Promise((resolve, reject) => {
    try {
      const wsUrl = `${getWebSocketUrl('/chat/ws')}?token=${encodeURIComponent(token)}`
      const ws = new WebSocket(wsUrl)

      const timer = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          try { ws.close() } catch {}
          reject(new Error('WebSocket connection timeout'))
        }
      }, 4000)

      ws.onopen = () => {
        clearTimeout(timer)
        sharedSocket = ws
        socketConnectingPromise = null
        resolve(ws)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (!isObject(data)) return

          const msgType = getString(data, 'type')
          if (msgType === 'status') {
            const statusText = getString(data, 'message')
            if (statusText && activeRequest?.onStatus) {
              activeRequest.onStatus(statusText)
            }
          } else if (msgType === 'response') {
            const id = getString(data, 'conversation_id', 'chat_id', 'id')
            const reply = getString(data, 'reply', 'response', 'assistant_message')
            if (id && reply) {
              const res: SendMessageResult = {
                id,
                title: getString(data, 'title'),
                updatedAt: getString(data, 'updated_at', 'updatedAt'),
                reply,
              }
              const current = activeRequest
              activeRequest = null
              current?.resolve(res)
            }
          } else if (msgType === 'error') {
            const detail = getString(data, 'detail', 'message') || 'An error occurred during consultation processing.'
            const current = activeRequest
            activeRequest = null
            current?.reject(new ApiError(detail))
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (err) => {
        clearTimeout(timer)
        socketConnectingPromise = null
        if (activeRequest) {
          const current = activeRequest
          activeRequest = null
          current.reject(new ApiError('DocPilot chat connection error.'))
        }
        reject(err)
      }

      ws.onclose = () => {
        clearTimeout(timer)
        sharedSocket = null
        socketConnectingPromise = null
        if (activeRequest) {
          const current = activeRequest
          activeRequest = null
          current.reject(new ApiError('Chat connection closed.'))
        }
      }
    } catch (err) {
      socketConnectingPromise = null
      reject(err)
    }
  })

  return socketConnectingPromise
}

function parseChatSummary(value: unknown): ChatSummary {
  if (!isObject(value)) throw new ApiError('The server returned an invalid conversation entry.')
  const id = getString(value, 'id', 'conversation_id', 'chat_id')
  if (!id) throw new ApiError('A conversation entry is missing its identifier.')

  return {
    id,
    title: getString(value, 'title', 'name') ?? 'Untitled conversation',
    updatedAt: getString(value, 'updated_at', 'updatedAt', 'created_at'),
  }
}

function parseChatList(value: unknown): ChatSummary[] {
  const rows = Array.isArray(value)
    ? value
    : isObject(value) && Array.isArray(value.chats)
      ? value.chats
      : isObject(value) && Array.isArray(value.items)
        ? value.items
        : undefined
  if (!rows) throw new ApiError('The server returned an invalid conversation history.')
  return rows.map(parseChatSummary)
}

function parseMessage(value: unknown): ChatMessage {
  if (!isObject(value)) throw new ApiError('The server returned an invalid conversation message.')
  const role = value.role
  const content = getString(value, 'content', 'message', 'text')
  if ((role !== 'user' && role !== 'assistant') || !content) {
    throw new ApiError('A conversation message is missing its role or content.')
  }
  return {
    id: getString(value, 'id', 'message_id'),
    role,
    content,
    createdAt: getString(value, 'created_at', 'createdAt'),
    attachments: Array.isArray(value.attachments)
      ? value.attachments.flatMap((attachment): ChatAttachment[] => {
          if (!isObject(attachment)) return []
          const filename = getString(attachment, 'filename')
          const fileType = getString(attachment, 'file_type')
          if (!filename || !fileType) return []
          return [{ filename, file_type: fileType, description: getString(attachment, 'description') }]
        })
      : [],
  }
}

function parseChatDetail(value: unknown): ChatDetail {
  const chat = isObject(value) && isObject(value.chat) ? value.chat : value
  if (!isObject(chat)) throw new ApiError('The server returned an invalid conversation.')
  const summary = parseChatSummary(chat)
  if (!Array.isArray(chat.messages)) throw new ApiError('The conversation response is missing its messages.')
  return { ...summary, messages: chat.messages.map(parseMessage) }
}

export async function getChats(): Promise<ChatSummary[]> {
  return parseChatList(await request(apiEndpoints.chats.list))
}

export async function getChat(id: string): Promise<ChatDetail> {
  return parseChatDetail(await request(apiEndpoints.chats.detail(id)))
}

export async function sendChatMessage(
  message: string,
  conversationId?: string,
  attachments: ChatAttachment[] = [],
  onStatus?: (status: string) => void,
): Promise<SendMessageResult> {
  // Try sending over WebSocket first for real-time bidirectional communication and live status streaming
  try {
    const ws = await getOrConnectChatSocket()
    if (ws.readyState === WebSocket.OPEN) {
      return await new Promise<SendMessageResult>((resolve, reject) => {
        activeRequest = { resolve, reject, onStatus }
        onStatus?.('DocPilot is thinking…')
        ws.send(JSON.stringify({
          type: 'message',
          message,
          ...(conversationId ? { conversation_id: conversationId } : {}),
          ...(attachments.length ? { attachments } : {}),
        }))
      })
    }
  } catch (wsErr) {
    console.warn('WebSocket chat unavailable, falling back to HTTP:', wsErr)
  }

  // Graceful fallback to HTTP POST if WebSocket is unavailable
  onStatus?.('DocPilot is thinking…')
  const body = await request(apiEndpoints.chats.send, {
    method: 'POST',
    body: JSON.stringify({
      message,
      ...(conversationId ? { conversation_id: conversationId } : {}),
      ...(attachments.length ? { attachments } : {}),
    }),
  })
  if (!isObject(body)) throw new ApiError('The server returned an invalid chat response.')

  const id = getString(body, 'conversation_id', 'chat_id', 'id')
  const reply = getString(body, 'reply', 'response', 'assistant_message')
  if (!id || !reply) {
    throw new ApiError('The chat response is missing its conversation identifier or reply.')
  }
  return {
    id,
    title: getString(body, 'title'),
    updatedAt: getString(body, 'updated_at', 'updatedAt'),
    reply,
  }
}
