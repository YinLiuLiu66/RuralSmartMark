// 车辆网格：在途车沿起讫站插值移动（tick.info 的 sim_time 驱动），停靠车摆在站点旁。
// 依据 M0 探针结论：正交相机 45° 俯视下起讫直线与公路曲线偏差可忽略，取直线求简。

import { useMemo, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

import type { SiteSnapshot, VehicleSnapshot } from '../api/types'

const PATH_Y = 0.34
// 车辆 id 取色（无美术素材的区分方案）
const PLATE_COLORS = ['#e2e8f0', '#f0a44a', '#67b7d1', '#c3a6ff']

function plateColor(id: number): string {
  return PLATE_COLORS[id % PLATE_COLORS.length]
}

function sitePos(sites: SiteSnapshot[], id: number): THREE.Vector3 | null {
  const s = sites.find((x) => x.id === id)
  return s ? new THREE.Vector3(s.pos_x, 0, s.pos_z) : null
}

function EnRouteVehicle({
  vehicle,
  sites,
  simTime,
  onSelect,
}: {
  vehicle: VehicleSnapshot
  sites: SiteSnapshot[]
  /** 模拟时间 epoch ms（tick.info 驱动；null = 尚无钟源，静止不插值） */
  simTime: number | null
  onSelect: (id: number) => void
}) {
  const ref = useRef<THREE.Mesh>(null)
  const route = vehicle.route

  const ends = useMemo(() => {
    if (!route) return null
    const from = sitePos(sites, route.from_site_id)
    const to = sitePos(sites, route.to_site_id)
    return from && to ? { from, to } : null
  }, [route, sites])

  const fraction = useMemo(() => {
    if (!route || simTime === null) return 0
    const start = Date.parse(route.departed_at)
    const end = Date.parse(route.arrives_at)
    if (!(end > start)) return 1
    return THREE.MathUtils.clamp((simTime - start) / (end - start), 0, 1)
  }, [route, simTime])

  useFrame(() => {
    const mesh = ref.current
    if (!mesh || !ends) return
    const p = ends.from.clone().lerp(ends.to, fraction)
    mesh.position.set(p.x, PATH_Y, p.z)
    const ahead = ends.from.clone().lerp(ends.to, Math.min(1, fraction + 0.01))
    mesh.lookAt(ahead.x, PATH_Y, ahead.z)
  })

  return (
    <mesh
      ref={ref}
      onClick={(e) => {
        e.stopPropagation()
        if (e.delta > 6) return
        onSelect(vehicle.id)
      }}
      onPointerOver={() => (document.body.style.cursor = 'pointer')}
      onPointerOut={() => (document.body.style.cursor = 'default')}
    >
      <boxGeometry args={[0.55, 0.32, 0.9]} />
      <meshStandardMaterial color={plateColor(vehicle.id)} />
    </mesh>
  )
}

function DockedVehicle({
  vehicle,
  site,
  onSelect,
}: {
  vehicle: VehicleSnapshot
  site: SiteSnapshot | undefined
  onSelect: (id: number) => void
}) {
  if (!site) return null
  return (
    <mesh
      position={[site.pos_x + 1.7, PATH_Y, site.pos_z + 1.2]}
      rotation={[0, Math.PI / 4, 0]}
      onClick={(e) => {
        e.stopPropagation()
        if (e.delta > 6) return
        onSelect(vehicle.id)
      }}
      onPointerOver={() => (document.body.style.cursor = 'pointer')}
      onPointerOut={() => (document.body.style.cursor = 'default')}
    >
      <boxGeometry args={[0.5, 0.3, 0.8]} />
      <meshStandardMaterial color={plateColor(vehicle.id)} />
    </mesh>
  )
}

export default function VehicleMeshes({
  vehicles,
  sites,
  simTime,
  onSelect,
}: {
  vehicles: VehicleSnapshot[]
  sites: SiteSnapshot[]
  /** 模拟时间 epoch ms；null = 无钟源 */
  simTime: number | null
  onSelect: (id: number) => void
}) {
  return (
    <group>
      {vehicles.map((v) =>
        v.status === 'en_route' && v.route ? (
          <EnRouteVehicle
            key={v.id}
            vehicle={v}
            sites={sites}
            simTime={simTime}
            onSelect={onSelect}
          />
        ) : (
          <DockedVehicle
            key={v.id}
            vehicle={v}
            site={sites.find((s) => s.id === v.current_site_id)}
            onSelect={onSelect}
          />
        ),
      )}
    </group>
  )
}
