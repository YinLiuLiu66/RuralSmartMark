// 详情卡：站点（库存/批次）/ 车辆（状态/温湿度/路线进度）/ 运单（五步 stepper）。
// 数据全部来自 M2 快照与 WS 合并后的 store。

import { useWorld } from '../stores/world'
import type { ShipmentSnapshot, VehicleSnapshot } from '../api/types'

const SHIPMENT_STEPS: { key: ShipmentSnapshot['status']; label: string }[] = [
  { key: 'confirmed', label: '已下单' },
  { key: 'picked', label: '已提货' },
  { key: 'loaded', label: '已装车' },
  { key: 'in_transit', label: '在途' },
  { key: 'delivered', label: '已送达' },
]

const SITE_TYPE_LABEL: Record<string, string> = {
  origin_hub: '产地',
  forward_warehouse: '前置仓',
  market: '门店',
}

const VEHICLE_STATUS_LABEL: Record<string, string> = {
  docking: '靠站待命',
  en_route: '在途配送',
  unloading: '卸货中',
  departed: '离站返程',
}

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false })
}

function ShipmentStepper({ shipment }: { shipment: ShipmentSnapshot }) {
  const idx = SHIPMENT_STEPS.findIndex((s) => s.key === shipment.status)
  return (
    <ol className="stepper">
      {SHIPMENT_STEPS.map((s, i) => (
        <li key={s.key} className={i <= idx ? 'done' : ''}>
          {s.label}
        </li>
      ))}
    </ol>
  )
}

export default function DetailCard({
  kind,
  id,
  onClose,
}: {
  kind: 'site' | 'vehicle' | 'shipment' | null
  id: number | null
  onClose: () => void
}) {
  const snapshot = useWorld((s) => s.snapshot)

  if (!snapshot || kind === null || id === null) {
    return (
      <aside className="probe-card">
        <p className="probe-card-empty">
          点击站点 / 车辆
          <br />
          查看实时详情卡
        </p>
      </aside>
    )
  }

  if (kind === 'site') {
    const site = snapshot.sites.find((s) => s.id === id)
    if (!site) return null
    const onSite = snapshot.pallets.filter((p) => p.current_site_id === id)
    return (
      <aside className="probe-card">
        <h2 style={{ color: '#7dd3fc' }}>{site.name}</h2>
        <dl>
          <div>
            <dt>类型</dt>
            <dd>{SITE_TYPE_LABEL[site.type] ?? site.type}</dd>
          </div>
          <div>
            <dt>在库托盘</dt>
            <dd>{onSite.length} 托</dd>
          </div>
          <div>
            <dt>批次</dt>
            <dd>{onSite.map((p) => p.batch_no).slice(0, 4).join('、') || '—'}</dd>
          </div>
        </dl>
        {onSite.length > 0 && (
          <ul className="card-list">
            {onSite.slice(0, 4).map((p) => (
              <li key={p.id}>{p.qty} 件 · {p.batch_no}</li>
            ))}
          </ul>
        )}
        <button type="button" onClick={onClose}>关闭</button>
      </aside>
    )
  }

  if (kind === 'vehicle') {
    const vehicle = snapshot.vehicles.find((v) => v.id === id) as
      | VehicleSnapshot
      | undefined
    if (!vehicle) return null
    const from = snapshot.sites.find((s) => s.id === vehicle.route?.from_site_id)
    const to = snapshot.sites.find((s) => s.id === vehicle.route?.to_site_id)
    const activeShipment = snapshot.shipments.find(
      (x) => x.vehicle_id === vehicle.id && x.status !== 'delivered',
    )
    return (
      <aside className="probe-card">
        <h2 style={{ color: '#fbbf24' }}>{vehicle.plate}</h2>
        <dl>
          <div>
            <dt>状态</dt>
            <dd>{VEHICLE_STATUS_LABEL[vehicle.status] ?? vehicle.status}</dd>
          </div>
          <div>
            <dt>货厢温度</dt>
            <dd>{vehicle.temperature != null ? `${vehicle.temperature} ℃` : '—'}</dd>
          </div>
          <div>
            <dt>湿度</dt>
            <dd>{vehicle.humidity != null ? `${vehicle.humidity} %` : '—'}</dd>
          </div>
          <div>
            <dt>路线</dt>
            <dd>
              {from && to ? `${from.name} → ${to.name}` : '—'}
              {vehicle.route &&
                `（${fmtTime(vehicle.route.departed_at)} → ${fmtTime(vehicle.route.arrives_at)}）`}
            </dd>
          </div>
        </dl>
        {activeShipment && <ShipmentStepper shipment={activeShipment} />}
        <button type="button" onClick={onClose}>关闭</button>
      </aside>
    )
  }

  const shipment = snapshot.shipments.find((s) => s.id === id)
  if (!shipment) return null
  const from = snapshot.sites.find((s) => s.id === shipment.from_site_id)
  const to = snapshot.sites.find((s) => s.id === shipment.to_site_id)
  return (
    <aside className="probe-card">
      <h2 style={{ color: '#a5b4fc' }}>运单 #{shipment.id}</h2>
      <dl>
        <div>
          <dt>路线</dt>
          <dd>{from && to ? `${from.name} → ${to.name}` : '—'}</dd>
        </div>
        <div>
          <dt>发车</dt>
          <dd>{fmtTime(shipment.departed_at)}</dd>
        </div>
        <div>
          <dt>送达</dt>
          <dd>{fmtTime(shipment.delivered_at)}</dd>
        </div>
      </dl>
      <ShipmentStepper shipment={shipment} />
      <button type="button" onClick={onClose}>关闭</button>
    </aside>
  )
}
