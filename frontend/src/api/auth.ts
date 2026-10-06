import { clearStoredToken, getStoredToken, request, setStoredToken } from './client'
import { apiEndpoints } from './endpoints'
import type { DoctorProfile, LoginCredentials, LoginResponse, RegisterCredentials, SignupResponse } from './types'

export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  const data = await request<LoginResponse>(apiEndpoints.auth.login, {
    method: 'POST',
    body: JSON.stringify({
      email: credentials.email.trim(),
      password: credentials.password,
    }),
  })
  if (data?.access_token) {
    setStoredToken(data.access_token)
  }
  return data
}

export async function register(credentials: RegisterCredentials): Promise<SignupResponse> {
  const fullName = (credentials.full_name || credentials.name || credentials.email.split('@')[0]).trim()
  const data = await request<SignupResponse>(apiEndpoints.auth.register, {
    method: 'POST',
    body: JSON.stringify({
      email: credentials.email.trim(),
      password: credentials.password,
      full_name: fullName,
    }),
  })
  if (data?.access_token) {
    setStoredToken(data.access_token)
  }
  return data
}

export async function logout(): Promise<void> {
  try {
    await request(apiEndpoints.auth.logout, { method: 'POST' })
  } catch {
    // If server logout fails or network dropped, clear local state regardless
  } finally {
    clearStoredToken()
  }
}

export async function getMe(): Promise<DoctorProfile> {
  return await request<DoctorProfile>(apiEndpoints.auth.me, { method: 'GET' })
}

export function isAuthenticated(): boolean {
  return Boolean(getStoredToken())
}

