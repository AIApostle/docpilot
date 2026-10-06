export interface ChatSummary {
  id: string
  title: string
  updatedAt?: string
}

export interface ChatMessage {
  id?: string
  role: 'user' | 'assistant'
  content: string
  createdAt?: string
}

export interface ChatDetail extends ChatSummary {
  messages: ChatMessage[]
}

export interface SendMessageResult {
  id: string
  title?: string
  updatedAt?: string
  reply: string
}
