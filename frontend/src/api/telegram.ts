import { request } from './client'
import { apiEndpoints } from './endpoints'
import type { TelegramConnectPayload, TelegramConnectionResult } from './types'

export async function connectTelegram(payload: TelegramConnectPayload): Promise<TelegramConnectionResult> {
  return await request<TelegramConnectionResult>(apiEndpoints.telegram.connect, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function disconnectTelegram(): Promise<void> {
  await request(apiEndpoints.telegram.disconnect, { method: 'POST' })
}
