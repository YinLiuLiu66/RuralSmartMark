// 沙盘实时态（decisions #8：Zustand 管 WS 增量流，TanStack 留给 REST 资源）。
// 快照全量打底 + WS 增量合并；ws 连接与重拉快照的副作用也收拢在这里。

import { create } from 'zustand'

import { fetchWorldSnapshot } from '../api/client'
import { connectWorldSocket, type WorldSocketHandle } from '../api/ws'
import type {
  EntityUpdatedData,
  SimClock,
  ShipmentSnapshot,
  WorldEvent,
  WorldSnapshot,
} from '../api/types'

interface WorldState {
  ready: boolean
  clock: SimClock | null
  snapshot: WorldSnapshot | null
  connect: () => void
  disconnect: () => void
  reload: () => Promise<void>
}

let handle: WorldSocketHandle | null = null

function applyEvent(state: WorldState, event: WorldEvent): Partial<WorldState> {
  const snap = state.snapshot
  if (!snap) return {}

  if (event.type === 'tick.info') {
    return { clock: event.data as SimClock }
  }

  if (event.type === 'entity.updated') {
    const { entity, id } = event.data as EntityUpdatedData
    if (entity === 'vehicle') {
      return {
        snapshot: {
          ...snap,
          vehicles: snap.vehicles.map((v) =>
            v.id === id ? { ...v, ...(event.data as EntityUpdatedData) } : v,
          ),
        },
      }
    }
    if (entity === 'worker') {
      return {
        snapshot: {
          ...snap,
          workers: snap.workers.map((w) =>
            w.id === id ? { ...w, ...(event.data as EntityUpdatedData) } : w,
          ),
        },
      }
    }
    return {
      snapshot: {
        ...snap,
        pallets: snap.pallets.map((p) =>
          p.id === id ? { ...p, ...(event.data as EntityUpdatedData) } : p,
        ),
      },
    }
  }

  if (event.type === 'shipment.progressed') {
    const s = event.data as unknown as ShipmentSnapshot
    const i = snap.shipments.findIndex((x) => x.id === s.id)
    const shipments = [...snap.shipments]
    if (i >= 0) shipments[i] = { ...shipments[i], ...s }
    else shipments.push(s)
    return { snapshot: { ...snap, shipments } }
  }

  return {}
}

export const useWorld = create<WorldState>((set, get) => ({
  ready: false,
  clock: null,
  snapshot: null,

  async reload() {
    const snapshot = await fetchWorldSnapshot()
    set({ snapshot, clock: snapshot.clock, ready: true })
  },

  connect() {
    if (handle) return
    handle = connectWorldSocket((event: WorldEvent) => {
      if (event.type === 'world.reset') {
        // 整个世界重建：本地合并无意义，重拉快照
        void get().reload()
        return
      }
      set((state) => applyEvent(state, event))
    })
  },

  disconnect() {
    handle?.close()
    handle = null
  },
}))
