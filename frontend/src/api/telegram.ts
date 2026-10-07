import { request } from './client'
import { apiEndpoints } from './endpoints'
import type { TelegramConnectPayload, TelegramConnectionResult, TelegramWidgetConfig } from './types'

export async function getTelegramWidgetConfig(): Promise<TelegramWidgetConfig> {
  return await request<TelegramWidgetConfig>(apiEndpoints.telegram.widgetConfig, { method: 'GET' })
}

export async function connectTelegram(payload: TelegramConnectPayload): Promise<TelegramConnectionResult> {
  return await request<TelegramConnectionResult>(apiEndpoints.telegram.connect, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function disconnectTelegram(): Promise<void> {
  await request(apiEndpoints.telegram.disconnect, { method: 'POST' })
}
