// 正式 3D 沙盘场景：相机/灯光/网格沿用 M0 探针结论，数据全部吃 M2 快照。
// 公路曲线与探针同款 CatmullRom（站点顺序即快照 id 序）。

import { useMemo } from 'react'
import * as THREE from 'three'
import { Canvas } from '@react-three/fiber'
import { Grid, Line, OrbitControls, OrthographicCamera } from '@react-three/drei'

import { useWorld } from '../stores/world'
import SiteMeshes from './SiteMeshes'
import VehicleMeshes from './VehicleMesh'

function Road({ sites }: { sites: { pos_x: number; pos_z: number }[] }) {
  const curve = useMemo(
    () =>
      new THREE.CatmullRomCurve3(
        sites.map((s) => new THREE.Vector3(s.pos_x, 0.05, s.pos_z)),
        false,
        'centripetal',
      ),
    [sites],
  )
  return (
    <Line
      points={curve.getPoints(140)}
      color="#8897b8"
      lineWidth={1.8}
      transparent
      opacity={0.9}
    />
  )
}

export default function WorldScene({
  selectedKind,
  selectedId,
  onSelect,
}: {
  selectedKind: 'site' | 'vehicle' | null
  selectedId: number | null
  onSelect: (kind: 'site' | 'vehicle', id: number) => void
}) {
  const snapshot = useWorld((s) => s.snapshot)
  const clock = useWorld((s) => s.clock)
  const sites = snapshot?.sites ?? []
  // tick 推进用模拟时间（epoch ms）；无任何钟源时为 null，车辆端自行静止
  const simTime = useMemo(() => {
    const t = clock?.sim_time ?? snapshot?.clock.sim_time
    return t ? Date.parse(t) : null
  }, [clock, snapshot])
  if (!snapshot) {
    return (
      <Canvas flat dpr={[1, 2]}>
        <color attach="background" args={['#0d1424']} />
      </Canvas>
    )
  }

  return (
    <Canvas flat dpr={[1, 2]}>
      <color attach="background" args={['#0d1424']} />
      {/* 45° 俯视正交相机（探针 pin 值：near 为负才不裁切放大场景） */}
      <OrthographicCamera makeDefault position={[11, 15.5, 11]} zoom={46} near={-80} far={300} />
      <ambientLight intensity={0.75} />
      <directionalLight position={[6, 12, 4]} intensity={1.15} />

      <Grid
        infiniteGrid
        cellSize={1}
        cellThickness={0.6}
        cellColor="#26304a"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#3a4767"
        fadeDistance={60}
        fadeStrength={1.6}
      />

      <Road sites={sites} />
      <SiteMeshes
        sites={sites}
        pallets={snapshot.pallets}
        selectedId={selectedKind === 'site' ? selectedId : null}
        onSelect={(id) => onSelect('site', id)}
      />
      <VehicleMeshes
        vehicles={snapshot.vehicles}
        sites={sites}
        simTime={simTime}
        onSelect={(id) => onSelect('vehicle', id)}
      />

      <OrbitControls
        enablePan={false}
        minZoom={22}
        maxZoom={110}
        maxPolarAngle={Math.PI / 2.25}
        target={[3, 0, 0]}
      />
    </Canvas>
  )
}
