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
    let detail: string | null = null
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // 非 JSON 错误体（代理/网关）走状态码兜底
    }
    throw new ApiError(detail ?? `请求失败: ${response.status}`, response.status)
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

// ---- 登录态（M4 工作台）----

const TOKEN_KEY = 'rsm_jwt'
const ROLE_KEY = 'rsm_role'
const USER_KEY = 'rsm_username'

export interface LoginResponse {
  access_token: string
  token_type: string
  role: string
  username: string
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export function getSession(): {
  token: string | null
  role: string | null
  username: string | null
} {
  return {
    token: getToken(),
    role: localStorage.getItem(ROLE_KEY),
    username: localStorage.getItem(USER_KEY),
  }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${BASE_URL}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  })
  if (!response.ok) {
    throw new ApiError('账号或密码错误', response.status)
  }
  const data = (await response.json()) as LoginResponse
  localStorage.setItem(TOKEN_KEY, data.access_token)
  localStorage.setItem(ROLE_KEY, data.role)
  localStorage.setItem(USER_KEY, data.username)
  return data
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_KEY)
}
