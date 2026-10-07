import { ApiError, isObject, request } from './client'
import { apiEndpoints } from './endpoints'
import type { MemoryPreference } from './types'

function parseMemoryPreference(value: unknown): MemoryPreference {
  if (!isObject(value) || typeof value.enabled !== 'boolean') {
    throw new ApiError('The server returned an invalid memory setting.')
  }
  return { enabled: value.enabled }
}

export async function getMemoryPreference(): Promise<MemoryPreference> {
  return parseMemoryPreference(await request(apiEndpoints.memory.preferences))
}

export async function updateMemoryPreference(enabled: boolean): Promise<MemoryPreference> {
  return parseMemoryPreference(await request(apiEndpoints.memory.preferences, {
    method: 'PUT',
    body: JSON.stringify({ enabled }),
  }))
}
