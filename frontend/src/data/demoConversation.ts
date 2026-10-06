import type { ChatDetail, ChatSummary } from '../api'
import { DEMO_CHAT_ID } from '../routes'

export const demoConversation: ChatDetail = {
  id: DEMO_CHAT_ID,
  title: 'Preview: DocPilot conversation',
  updatedAt: '2026-10-05T09:30:00.000Z',
  messages: [
    {
      id: 'demo-user-message',
      role: 'user',
      content: 'What can I use DocPilot for?',
      createdAt: '2026-10-05T09:29:00.000Z',
    },
    {
      id: 'demo-assistant-message',
      role: 'assistant',
      content: 'This is a local interface preview. Once the API is connected and you sign in, DocPilot can help retrieve and update information that has been documented. No message in this preview is sent or saved.',
      createdAt: '2026-10-05T09:30:00.000Z',
    },
  ],
}

export const demoHistory: ChatSummary[] = [{
  id: demoConversation.id,
  title: demoConversation.title,
  updatedAt: demoConversation.updatedAt,
}]
