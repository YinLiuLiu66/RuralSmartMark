// 公开溯源接口（M5）：固定演示码 + 当前 origin 下的二维码 URL。

import { request } from './client'
import type { TraceResponse } from './types'

export const DEMO_TRACE_CODE = 'MJDEMO22'

export function fetchTrace(code: string): Promise<TraceResponse> {
  return request<TraceResponse>(`/api/trace/${encodeURIComponent(code)}`)
}

export function tracePageUrl(code: string): string {
  return `${window.location.origin}/t/${encodeURIComponent(code)}`
}
