// 站点与库存：坐标/库存全部来自 M2 快照（真实世界），不再用探针假数据。
// 探针结论沿用：点击 e.delta>6 防拖动误触；选中放大 + 自发光。

import { useRef } from 'react'
import { useFrame, type ThreeEvent } from '@react-three/fiber'
import type * as THREE from 'three'

import type { PalletSnapshot, SiteSnapshot } from '../api/types'

// 探针同款四色：站点按快照序（farm → hub → depot → market）取色，
// 类型色会把农场与集货仓都染成 origin_hub 绿，辨识度差
const SITE_COLORS = ['#6aa84f', '#d97706', '#0ea5e9', '#8b5cf6']

function SiteMesh({
  site,
  siteIndex,
  palletCount,
  selected,
  onSelect,
}: {
  site: SiteSnapshot
  siteIndex: number
  palletCount: number
  selected: boolean
  onSelect: (id: number) => void
}) {
  const boxRef = useRef<THREE.Mesh>(null)
  const color = SITE_COLORS[siteIndex % SITE_COLORS.length]
  // 库存映射高度：0 托 0.6、≥16 托 2.2（线性截断）
  const height = 0.6 + Math.min(palletCount, 16) * 0.1

  useFrame((_, delta) => {
    const mesh = boxRef.current
    if (!mesh) return
    const target = selected ? 1.12 : 1
    const next = mesh.scale.x + (target - mesh.scale.x) * Math.min(1, delta * 10)
    mesh.scale.setScalar(next)
  })

  return (
    <group position={[site.pos_x, 0, site.pos_z]}>
      <mesh position={[0, 0.12, 0]}>
        <boxGeometry args={[2, 0.24, 2]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      <mesh
        ref={boxRef}
        position={[0, 0.24 + height / 2, 0]}
        onClick={(e: ThreeEvent<MouseEvent>) => {
          e.stopPropagation()
          if (e.delta > 6) return
          onSelect(site.id)
        }}
        onPointerOver={() => (document.body.style.cursor = 'pointer')}
        onPointerOut={() => (document.body.style.cursor = 'default')}
      >
        <boxGeometry args={[1.5, height, 1.5]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 0.45 : 0.08}
        />
      </mesh>
    </group>
  )
}

export default function SiteMeshes({
  sites,
  pallets,
  selectedId,
  onSelect,
}: {
  sites: SiteSnapshot[]
  pallets: PalletSnapshot[]
  selectedId: number | null
  onSelect: (id: number) => void
}) {
  const countBySite = new Map<number, number>()
  for (const p of pallets) {
    if (p.current_site_id != null) {
      countBySite.set(p.current_site_id, (countBySite.get(p.current_site_id) ?? 0) + 1)
    }
  }

  return (
    <group>
      {sites.map((s, i) => (
        <SiteMesh
          key={s.id}
          site={s}
          siteIndex={i}
          palletCount={countBySite.get(s.id) ?? 0}
          selected={s.id === selectedId}
          onSelect={onSelect}
        />
      ))}
    </group>
  )
}
