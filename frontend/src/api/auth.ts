import { request } from './client'
import { apiEndpoints } from './endpoints'

export async function login(credentials: { email: string; password: string }): Promise<void> {
  await request(apiEndpoints.auth.login, {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export async function register(credentials: { name?: string; email: string; password: string }): Promise<void> {
  await request(apiEndpoints.auth.register, {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export async function logout(): Promise<void> {
  await request(apiEndpoints.auth.logout, { method: 'POST' })
}
