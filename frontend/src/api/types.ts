// 与后端 docs/03-data-model.md §3.1 对齐的世界数据类型（M2 快照 + WS 事件封套）

export interface SimClock {
  sim_time: string
  speed: number
  running: boolean
  tick: number
}

export type SiteType = 'origin_hub' | 'forward_warehouse' | 'market'

export interface SiteSnapshot {
  id: number
  name: string
  type: SiteType
  status: string
  capacity: number
  pos_x: number
  pos_z: number
}

export interface VehicleRoute {
  from_site_id: number
  to_site_id: number
  /** 模拟时间 ISO 字符串（带时区） */
  departed_at: string
  arrives_at: string
}

export type VehicleStatus = 'en_route' | 'docking' | 'unloading' | 'departed'

export interface VehicleSnapshot {
  id: number
  plate: string
  status: VehicleStatus
  temperature: number | null
  humidity: number | null
  current_site_id: number | null
  route: VehicleRoute | null
}

export type WorkerStatus = 'idle' | 'sorting' | 'loading' | 'off_duty'

export interface WorkerSnapshot {
  id: number
  site_id: number
  name: string
  status: WorkerStatus
  moves_today: number
}

export interface PalletSnapshot {
  id: number
  sku_id: number | null
  qty: number
  batch_no: string
  current_site_id: number | null
  current_vehicle_id: number | null
}

export type ShipmentStatus = 'confirmed' | 'picked' | 'loaded' | 'in_transit' | 'delivered'

export interface ShipmentSnapshot {
  id: number
  from_site_id: number
  to_site_id: number
  vehicle_id: number
  status: ShipmentStatus
  departed_at: string | null
  delivered_at: string | null
}

export interface WorldSnapshot {
  clock: SimClock
  sites: SiteSnapshot[]
  vehicles: VehicleSnapshot[]
  workers: WorkerSnapshot[]
  pallets: PalletSnapshot[]
  shipments: ShipmentSnapshot[]
}

// ---- WS 事件封套：{type, sim_time, data}（03 §3.3）----

export interface EventEnvelope<T = Record<string, unknown>> {
  type: string
  sim_time: string
  data: T
}

export type EntityUpdatedData = {
  entity: 'vehicle' | 'worker' | 'pallet'
  id: number
  route?: VehicleRoute | null
} & Partial<VehicleSnapshot> &
  Partial<WorkerSnapshot> &
  Partial<PalletSnapshot>

export interface ShipmentProgressedData extends ShipmentSnapshot {}

export type WorldEvent =
  | EventEnvelope<SimClock> // tick.info
  | EventEnvelope<EntityUpdatedData> // entity.updated
  | EventEnvelope<ShipmentProgressedData> // shipment.progressed
  | EventEnvelope<Record<string, unknown>> // world.reset / agent.*（M4）

// ---- Agent 任务与产出物（03 §3.2，M4）----

export type AgentStatus = 'pending' | 'running' | 'done' | 'failed'
export type ArtifactStatus = 'draft' | 'polished' | 'final'

export interface AgentArtifact {
  id: number
  kind: 'story' | 'copy' | 'design'
  content: string | null
  asset_url: string | null
  status: ArtifactStatus
  updated_at: string
}

export interface AgentTask {
  id: number
  agent_type: 'story' | 'copy'
  status: AgentStatus
  product_sku_id: number | null
  created_by: string
  created_at: string
  updated_at: string
  artifacts: AgentArtifact[]
}

// ---- 溯源 H5（M5，decisions #30）----

export interface TraceProduct {
  sku_id: number
  name: string
  box_price: number
  batch_no: string
  qty: number
}

export interface TraceStory {
  artifact_id: number
  content: string
}

export interface TraceEvent {
  id: number
  kind: string
  label: string
  sim_time: string | null
  site_name: string | null
  vehicle_plate: string | null
  note: string | null
  temperature: number | null
}

export interface TraceResponse {
  code: string
  is_demo: boolean
  product: TraceProduct
  story: TraceStory | null
  timeline: TraceEvent[]
}

// ---- 溢价对照（M6，decisions #31）----

export interface PriceBenchmark {
  channel: string
  bulk_price: number
  brand_price: number
  premium_rate: number
}

export interface PricingResponse {
  sku_id: number
  sku_name: string
  note: string
  items: PriceBenchmark[]
}
