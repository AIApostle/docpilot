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
  attachments?: ChatAttachment[]
}

export interface ChatAttachment {
  filename: string
  file_type: string
  content_base64?: string
  description?: string
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

export interface MemoryPreference {
  enabled: boolean
}

export interface DoctorSummary {
  id: string
  email: string
  full_name?: string | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
  doctor?: DoctorSummary
}

export interface SignupResponse {
  doctor_id: string
  email: string
  full_name?: string | null
  access_token: string
  token_type: string
}

export interface DoctorProfile {
  sub: string
  email?: string | null
  full_name?: string | null
  role?: string | null
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  name?: string
  full_name?: string
  email: string
  password: string
}

export interface TelegramConnectPayload {
  id: number
  first_name: string
  last_name?: string
  username?: string
  photo_url?: string
  auth_date: number
  hash: string
}

export interface TelegramWidgetConfig {
  bot_username: string
}

export interface TelegramConnectionResult {
  status: string
  doctor_id: string
  telegram_user_id: number
}
