import { useRef } from 'react'
import * as THREE from 'three'
import { Canvas, useFrame, type ThreeEvent } from '@react-three/fiber'
import { Grid, Line, OrbitControls, OrthographicCamera } from '@react-three/drei'
import { SITES, type SiteData } from './probeData'

const PATH_Y = 0.05

const pathCurve = new THREE.CatmullRomCurve3(
  SITES.map((s) => new THREE.Vector3(s.position[0], PATH_Y, s.position[2])),
  false,
  'centripetal',
)

/** 沿路径弧长匀速滑动的小车（冷链车占位） */
function Truck({ phase, color, speed = 0.04 }: { phase: number; color: string; speed?: number }) {
  const ref = useRef<THREE.Mesh>(null)

  useFrame(({ clock }) => {
    const mesh = ref.current
    if (!mesh) return
    const u = (clock.elapsedTime * speed + phase) % 1
    const p = pathCurve.getPointAt(u)
    mesh.position.set(p.x, 0.24, p.z)
    const ahead = pathCurve.getPointAt((u + 0.002) % 1)
    mesh.lookAt(ahead.x, 0.24, ahead.z)
  })

  return (
    <mesh ref={ref}>
      <boxGeometry args={[0.55, 0.32, 0.9]} />
      <meshStandardMaterial color={color} />
    </mesh>
  )
}

function Site({
  site,
  selected,
  onSelect,
}: {
  site: SiteData
  selected: boolean
  onSelect: (id: string) => void
}) {
  const boxRef = useRef<THREE.Mesh>(null)

  useFrame((_, delta) => {
    const mesh = boxRef.current
    if (!mesh) return
    const target = selected ? 1.12 : 1
    const next = mesh.scale.x + (target - mesh.scale.x) * Math.min(1, delta * 10)
    mesh.scale.setScalar(next)
  })

  return (
    <group position={site.position}>
      {/* 底座 */}
      <mesh position={[0, 0.12, 0]}>
        <boxGeometry args={[2, 0.24, 2]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      {/* 站点主体 */}
      <mesh
        ref={boxRef}
        position={[0, 0.79, 0]}
        onClick={(e: ThreeEvent<MouseEvent>) => {
          e.stopPropagation()
          // 拖动旋转结束落在方块上的误触不当作点击
          if (e.delta > 6) return
          onSelect(site.id)
        }}
        onPointerOver={() => {
          document.body.style.cursor = 'pointer'
        }}
        onPointerOut={() => {
          document.body.style.cursor = 'default'
        }}
      >
        <boxGeometry args={[1.5, 1.1, 1.5]} />
        <meshStandardMaterial
          color={site.color}
          emissive={site.color}
          emissiveIntensity={selected ? 0.45 : 0.08}
        />
      </mesh>
    </group>
  )
}

export default function ProbeScene({
  selectedId,
  onSelect,
}: {
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <Canvas flat dpr={[1, 2]}>
      <color attach="background" args={['#0d1424']} />
      {/* 45° 俯视正交相机：[11, 15.5, 11] 仰角 ≈ 45°，等距沙盘感 */}
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

      {/* 站点连线（公路占位） */}
      <Line
        points={pathCurve.getPoints(140)}
        color="#8897b8"
        lineWidth={1.8}
        transparent
        opacity={0.9}
      />

      {SITES.map((s) => (
        <Site key={s.id} site={s} selected={s.id === selectedId} onSelect={onSelect} />
      ))}

      <Truck phase={0} color="#e2e8f0" />
      <Truck phase={0.47} color="#f0a44a" />

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
