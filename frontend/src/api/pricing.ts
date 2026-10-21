// 公开溢价对照接口（M6，decisions #31）。

import { request } from './client'
import type { PricingResponse } from './types'

export function fetchPricing(): Promise<PricingResponse> {
  return request<PricingResponse>('/api/pricing/benchmarks')
}
