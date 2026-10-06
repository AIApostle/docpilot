import { ApiError, getString, isObject, request } from './client'
import { apiEndpoints } from './endpoints'
import type { ChatDetail, ChatMessage, ChatSummary, SendMessageResult } from './types'

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

export async function sendChatMessage(message: string, conversationId?: string): Promise<SendMessageResult> {
  const body = await request(apiEndpoints.chats.send, {
    method: 'POST',
    body: JSON.stringify({
      message,
      ...(conversationId ? { conversation_id: conversationId } : {}),
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
