// WS 客户端：连 /ws/world 增量流，断线自动重连（指数退避）。
// 事件交给 store 合并；world.reset 由上层决定重拉快照。

import type { WorldEvent } from './types'

const WS_PATH = '/ws/world'
const MAX_BACKOFF_MS = 10000

export interface WorldSocketHandle {
  close(): void
}

export function connectWorldSocket(onEvent: (event: WorldEvent) => void): WorldSocketHandle {
  let ws: WebSocket | null = null
  let retry = 0
  let closed = false
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  const open = () => {
    if (closed) return
    // 相对地址自动继承页面协议与 host（dev 走 vite 代理，生产走同源反代）
    ws = new WebSocket(new URL(WS_PATH, location.href).toString().replace(/^http/, 'ws'))

    ws.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data as string) as WorldEvent)
      } catch {
        // 单条坏消息直接丢弃，不断链路
      }
    }
    ws.onopen = () => {
      retry = 0
    }
    ws.onclose = () => {
      if (closed) return
      const delay = Math.min(500 * 2 ** retry, MAX_BACKOFF_MS)
      retry += 1
      reconnectTimer = setTimeout(open, delay)
    }
    // onerror 后浏览器必发 onclose，交给 onclose 统一重连
  }

  open()

  return {
    close() {
      closed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      ws?.close()
    },
  }
}
