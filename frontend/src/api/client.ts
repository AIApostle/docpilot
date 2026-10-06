type JsonObject = Record<string, unknown>

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim().replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status?: number
  readonly code?: string

  constructor(message: string, status?: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export function isObject(value: unknown): value is JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function getString(object: JsonObject, ...keys: string[]): string | undefined {
  for (const key of keys) {
    const value = object[key]
    if (typeof value === 'string' && value.trim()) return value.trim()
  }
  return undefined
}

function defaultErrorMessage(status: number): string {
  if (status === 401) return 'Your session has ended. Sign in again to continue.'
  if (status === 403) return 'You do not have access to this conversation.'
  if (status === 404) return 'The requested resource could not be found.'
  if (status >= 500) return 'DocPilot is having trouble right now. Try again in a moment.'
  return `The request could not be completed (error ${status}). Check your details and try again.`
}

function apiErrorFromResponse(body: unknown, status: number): ApiError {
  if (isObject(body)) {
    const message = getString(body, 'detail', 'message', 'title', 'error')
    const code = getString(body, 'code', 'error_code')
    if (message) return new ApiError(message, status, code)
  }
  if (typeof body === 'string' && body.trim()) return new ApiError(body.trim(), status)
  return new ApiError(defaultErrorMessage(status), status)
}

async function readResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined

  const text = await response.text()
  if (!text.trim()) return undefined

  const contentType = response.headers.get('content-type') ?? ''
  if (contentType.includes('json')) {
    try {
      return JSON.parse(text) as unknown
    } catch {
      if (!response.ok) return undefined
      throw new ApiError('The server returned invalid JSON. Check the API response format.', response.status)
    }
  }

  return text
}

function makeUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${apiBaseUrl}${normalizedPath}`
}

export async function request(path: string, init: RequestInit = {}): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(makeUrl(path), {
      ...init,
      credentials: init.credentials ?? 'include',
      headers: {
        Accept: 'application/json',
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    })
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error
    throw new ApiError('DocPilot could not reach the server. Check your connection and try again.')
  }

  let body: unknown
  try {
    body = await readResponseBody(response)
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError('The server response could not be read. Try again or check the API configuration.', response.status)
  }

  if (!response.ok) throw apiErrorFromResponse(body, response.status)
  return body
}
