import type { SimClock, WorldSnapshot } from './types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })

  if (!response.ok) {
    throw new ApiError(`请求失败: ${response.status}`, response.status)
  }

  return (await response.json()) as T
}

export interface HealthResponse {
  status: string
  service: string
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

export function fetchWorldSnapshot(): Promise<WorldSnapshot> {
  return request<WorldSnapshot>('/api/world/snapshot')
}

export function simControl(action: string, speed?: number): Promise<{ clock: SimClock }> {
  return request<{ clock: SimClock }>('/api/sim/control', {
    method: 'POST',
    headers: { Authorization: `Bearer ${localStorage.getItem('rsm_jwt') ?? ''}` },
    body: JSON.stringify({ action, speed }),
  })
}

export function saveToken(token: string): void {
  localStorage.setItem('rsm_jwt', token)
}
