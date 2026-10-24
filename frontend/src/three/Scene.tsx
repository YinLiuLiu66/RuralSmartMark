import { Html, OrbitControls, RoundedBox, useCursor, useTexture } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import type { StationStatus } from "../agents";
import { STATIONS, type StationMeta, type Vec3 } from "./stations";

const STATUS_LABEL: Record<StationStatus, string> = {
  idle: "待运行",
  running: "生成中",
  review: "待审核",
  done: "已通过",
  failed: "失败",
};

const STATUS_COLOR: Record<StationStatus, string> = {
  idle: "#8A8A80",
  running: "#B6402A",
  review: "#8A5A00",
  done: "#3F6B4F",
  failed: "#B3261E",
};

const BATCH_POSITIONS: Record<string, Vec3> = {
  intake: [-3, 0, -4],
  story: [-9, 0, 2.8],
  packaging: [0, 0, 5.8],
  marketing: [8, 0, 1.8],
  pricing: [14, 0, 6.8],
  trace: [14, 0, 7.8],
};

const STATION_ORDER = Object.keys(BATCH_POSITIONS);

const BATCH_PATH = new THREE.CatmullRomCurve3(
  Object.values(BATCH_POSITIONS).map((point) => new THREE.Vector3(...point)),
  false,
  "catmullrom",
  0.32,
);

const BATCH_LABEL: Record<string, string> = {
  intake: "原料",
  story: "故事 IP",
  packaging: "包装",
  marketing: "内容",
  pricing: "定价",
  trace: "溯源",
};

function KraftBox() {
  return (
    <mesh position={[0, 0.74, 0]} castShadow>
      <boxGeometry args={[1.45, 0.98, 1.15]} />
      <meshStandardMaterial color="#C9A46A" />
    </mesh>
  );
}

function Tree({ position }: { position: Vec3 }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.55, 0]} castShadow>
        <cylinderGeometry args={[0.1, 0.14, 1.1, 6]} />
        <meshStandardMaterial color="#8A6A4A" />
      </mesh>
      <mesh position={[0, 1.45, 0]} castShadow>
        <sphereGeometry args={[0.78, 10, 8]} />
        <meshStandardMaterial color="#4F7A5A" />
      </mesh>
      <mesh position={[0.36, 1.22, 0.2]} castShadow>
        <sphereGeometry args={[0.26, 8, 6]} />
        <meshStandardMaterial color="#B6402A" />
      </mesh>
    </group>
  );
}

function Orchard() {
  return (
    <group>
      {Array.from({ length: 4 }).map((_, row) =>
        Array.from({ length: 4 }).map((__, col) => (
          <Tree
            key={`${row}-${col}`}
            position={[-17 + row * 2.2, 0, -9 + col * 2.2]}
          />
        )),
      )}
    </group>
  );
}

function StationBuilding({
  station,
  status,
  onSelect,
}: {
  station: StationMeta;
  status: StationStatus;
  onSelect?: (stationId: string) => void;
}) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  return (
    <group
      position={station.position}
      onClick={(event) => {
        event.stopPropagation();
        onSelect?.(station.id);
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      <mesh position={[0, 0.06, 0]} receiveShadow>
        <boxGeometry args={[3.0, 0.12, 2.4]} />
        <meshStandardMaterial color="#D9D2C0" />
      </mesh>
      <RoundedBox
        position={[0, 0.82, 0]}
        args={[2.8, 1.5, 2.2]}
        radius={0.12}
        smoothness={4}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial color="#FFFDF8" />
      </RoundedBox>
      <mesh position={[0, 2.02, 0]} rotation={[0, Math.PI / 4, 0]} castShadow>
        <coneGeometry args={[2.15, 0.95, 4]} />
        <meshStandardMaterial color={station.color} />
      </mesh>
      <mesh position={[0, 0.58, 1.12]}>
        <boxGeometry args={[0.72, 1.0, 0.06]} />
        <meshStandardMaterial color="#8A6A4A" />
      </mesh>
      <mesh position={[0, 1.28, 1.12]}>
        <boxGeometry args={[1.0, 0.3, 0.06]} />
        <meshStandardMaterial color="#C9A46A" />
      </mesh>
      <mesh position={[0, 2.58, 0]} castShadow>
        <sphereGeometry args={[0.11, 12, 12]} />
        <meshStandardMaterial
          color={STATUS_COLOR[status]}
          emissive={STATUS_COLOR[status]}
          emissiveIntensity={status === "running" ? 1.2 : 0.2}
        />
      </mesh>
      <Html position={[0, 3.0, 0]} center style={{ pointerEvents: "none" }}>
        <div className="flex items-center gap-1.5 whitespace-nowrap rounded-full border border-line bg-surface/95 px-3 py-1 text-[11px] font-medium text-ink shadow-card">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: STATUS_COLOR[status] }}
          />
          {station.name}
          <span className="font-normal text-ink-faint">· {STATUS_LABEL[status]}</span>
        </div>
      </Html>
    </group>
  );
}

function TexturedGiftBox({ imageUrl }: { imageUrl: string }) {
  const texture = useTexture(imageUrl);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;

  return (
    <mesh position={[0, 0.74, 0]} castShadow>
      <boxGeometry args={[1.45, 0.98, 1.15]} />
      <meshStandardMaterial attach="material-0" color="#C9A46A" />
      <meshStandardMaterial attach="material-1" color="#C9A46A" />
      <meshStandardMaterial attach="material-2" color="#C9A46A" />
      <meshStandardMaterial attach="material-3" color="#C9A46A" />
      <meshStandardMaterial attach="material-4" map={texture} toneMapped={false} />
      <meshStandardMaterial attach="material-5" map={texture} toneMapped={false} />
    </mesh>
  );
}

function BatchPallet({
  code,
  station,
  packagingImageUrl,
  onClick,
}: {
  code: string;
  station: string;
  packagingImageUrl: string | null;
  onClick?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  const groupRef = useRef<THREE.Group>(null);
  const initialized = useRef(false);
  const targetIndex = Math.max(0, STATION_ORDER.indexOf(station));
  const targetT = targetIndex / (STATION_ORDER.length - 1);
  const progress = useRef(targetT);
  const label = BATCH_LABEL[station] ?? "原料";
  useCursor(hovered);

  useEffect(() => {
    if (!initialized.current && groupRef.current) {
      groupRef.current.position.copy(BATCH_PATH.getPointAt(targetT));
      initialized.current = true;
    }
  }, [targetT]);

  useFrame((_, delta) => {
    progress.current = THREE.MathUtils.damp(progress.current, targetT, 2.6, delta);
    const point = BATCH_PATH.getPointAt(THREE.MathUtils.clamp(progress.current, 0, 1));
    groupRef.current?.position.copy(point);
  });

  return (
    <group
      ref={groupRef}
      onClick={(event) => {
        event.stopPropagation();
        onClick?.();
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      <mesh position={[0, 0.13, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.8, 0.26, 1.3]} />
        <meshStandardMaterial color="#C9A46A" />
      </mesh>
      {packagingImageUrl ? (
        <Suspense fallback={<KraftBox />}>
          <TexturedGiftBox imageUrl={packagingImageUrl} />
        </Suspense>
      ) : (
        <mesh position={[0, 0.7, 0]} castShadow>
          <boxGeometry args={[1.35, 0.9, 1.05]} />
          <meshStandardMaterial color="#E7D8BF" />
        </mesh>
      )}
      {!packagingImageUrl && (
        <Html position={[0, 1.55, 0]} center style={{ pointerEvents: "none" }}>
          <div className="whitespace-nowrap rounded-full border border-apple/30 bg-apple-weak px-3 py-1 text-[11px] font-medium text-apple shadow-card">
            {code} · {label}
          </div>
        </Html>
      )}
    </group>
  );
}

function Billboard({
  title,
  ready,
  onSelect,
}: {
  title: string;
  ready: boolean;
  onSelect?: () => void;
}) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  return (
    <group
      position={[-3, 0, 16]}
      onClick={(event) => {
        event.stopPropagation();
        onSelect?.();
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[1.7, 0.1, 1.0]} />
        <meshStandardMaterial color="#8A8578" />
      </mesh>
      {[-0.52, 0.52].map((x) => (
        <mesh key={x} position={[x, 1.55, 0]} castShadow>
          <cylinderGeometry args={[0.05, 0.06, 3.1, 8]} />
          <meshStandardMaterial color="#5F655F" />
        </mesh>
      ))}
      <Html position={[0, 2.8, 0.2]} center style={{ pointerEvents: "none", width: "200px" }}>
        <div className="rounded-sm border border-line bg-surface/95 px-3 py-2.5 shadow-card">
          <div className="text-[9px] uppercase tracking-[0.18em] text-apple">
            内容工坊 · 小红书封面
          </div>
          <div className="mt-1.5 font-display text-lg leading-snug text-ink">{title}</div>
          <div className="mt-1 text-[9px] text-ink-faint">
            {ready ? "来自内容 Agent 的标题" : "等待内容工坊产出"}
          </div>
        </div>
      </Html>
    </group>
  );
}

function QrSign({ traceCode, onOpen }: { traceCode: string; onOpen?: () => void }) {
  const [hovered, setHovered] = useState(false);
  useCursor(hovered);

  return (
    <group
      position={[21, 0, 7]}
      onClick={(event) => {
        event.stopPropagation();
        onOpen?.();
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      <mesh position={[0, 0.05, 0]} receiveShadow>
        <boxGeometry args={[1.7, 0.1, 1.0]} />
        <meshStandardMaterial color="#8A8578" />
      </mesh>
      <mesh position={[0, 1.55, 0]} castShadow>
        <boxGeometry args={[1.9, 3.0, 0.12]} />
        <meshStandardMaterial color="#FFFDF8" />
      </mesh>
      <Html position={[0, 2.0, 0.2]} center style={{ pointerEvents: "auto" }}>
        <button
          type="button"
          onClick={(event) => {
            event.stopPropagation();
            onOpen?.();
          }}
          aria-label="打开溯源页"
          title="打开溯源页"
          className="cursor-pointer rounded-sm border border-line bg-white p-1.5 shadow-card transition-all hover:-translate-y-0.5 hover:border-apple/40 hover:shadow-lg"
        >
          <img
            src={`/api/trace/${traceCode}/qr.png`}
            alt={`溯源码 ${traceCode}`}
            className="block"
            style={{ width: 84, height: 84, maxWidth: "none" }}
          />
        </button>
      </Html>
      <Html position={[0, 0.65, 0.2]} center style={{ pointerEvents: "none" }}>
        <div className="whitespace-nowrap rounded-full border border-line bg-surface/95 px-2.5 py-1 text-[10px] text-ink-muted shadow-card">
          扫码看溯源
        </div>
      </Html>
    </group>
  );
}

function Truck({ moving }: { moving: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const target = useMemo(
    () => new THREE.Vector3(moving ? 19 : 10, 0, moving ? 10 : 7.4),
    [moving],
  );

  useFrame((_, delta) => {
    groupRef.current?.position.lerp(target, 1 - Math.exp(-delta * 2.2));
  });

  return (
    <group ref={groupRef} position={[10, 0, 7.4]}>
      <mesh position={[0, 0.55, 0]} castShadow>
        <boxGeometry args={[2.2, 1.0, 1.1]} />
        <meshStandardMaterial color="#FFFDF8" />
      </mesh>
      <mesh position={[1.4, 0.45, 0]} castShadow>
        <boxGeometry args={[0.8, 0.8, 1.0]} />
        <meshStandardMaterial color="#B6402A" />
      </mesh>
      {[-0.65, 0.65].map((x) => (
        <mesh key={x} position={[x, 0.12, 0.58]} castShadow>
          <cylinderGeometry args={[0.22, 0.22, 0.18, 12]} />
          <meshStandardMaterial color="#1F2A24" />
        </mesh>
      ))}
    </group>
  );
}

function Stations({
  statuses,
  onSelect,
}: {
  statuses: Record<string, StationStatus>;
  onSelect?: (stationId: string) => void;
}) {
  return (
    <>
      {STATIONS.map((station) => (
        <StationBuilding
          key={station.id}
          station={station}
          status={statuses[station.id] ?? "idle"}
          onSelect={onSelect}
        />
      ))}
    </>
  );
}

function SceneContent({
  batchCode,
  batchStation,
  stationStatuses,
  packagingImageUrl,
  marketingTitle,
  traceCode,
  traced,
  onSelectBatch,
  onSelectStation,
  onOpenTrace,
}: {
  batchCode: string;
  batchStation: string;
  stationStatuses: Record<string, StationStatus>;
  packagingImageUrl: string | null;
  marketingTitle: string | null;
  traceCode: string | null;
  traced: boolean;
  onSelectBatch?: () => void;
  onSelectStation?: (stationId: string) => void;
  onOpenTrace?: () => void;
}) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  if (!ready) return null;

  return (
    <>
      <Stations statuses={stationStatuses} onSelect={onSelectStation} />
      <Billboard
        title={marketingTitle ?? "内容工坊"}
        ready={Boolean(marketingTitle)}
        onSelect={() => onSelectStation?.("marketing")}
      />
      <BatchPallet
        code={batchCode}
        station={batchStation}
        packagingImageUrl={packagingImageUrl}
        onClick={onSelectBatch}
      />
      <Truck moving={traced} />
      {traceCode && <QrSign traceCode={traceCode} onOpen={onOpenTrace} />}
    </>
  );
}

export function Scene({
  batchCode,
  batchStation,
  stationStatuses,
  packagingImageUrl = null,
  marketingTitle = null,
  traceCode = null,
  traced = false,
  onSelectBatch,
  onSelectStation,
  onOpenTrace,
}: {
  batchCode: string;
  batchStation: string;
  stationStatuses: Record<string, StationStatus>;
  packagingImageUrl?: string | null;
  marketingTitle?: string | null;
  traceCode?: string | null;
  traced?: boolean;
  onSelectBatch?: () => void;
  onSelectStation?: (stationId: string) => void;
  onOpenTrace?: () => void;
}) {
  return (
    <Canvas
      orthographic
      shadows
      dpr={[1, 2]}
      camera={{
        position: [18, 18, 18],
        zoom: 1,
        left: -20,
        right: 20,
        top: 17.5,
        bottom: -17.5,
        near: 0.1,
        far: 1000,
      }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
      style={{ background: "#F7F3EA" }}
    >
      <hemisphereLight args={["#FFF6E5", "#B7C4A8", 0.75]} />
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[12, 16, 8]}
        intensity={1.5}
        castShadow
        shadow-mapSize={[1024, 1024]}
      />

      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[48, 36]} />
        <meshStandardMaterial color="#E7E0CF" />
      </mesh>
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[-14, 0.02, -7]}
        receiveShadow
      >
        <planeGeometry args={[12, 10]} />
        <meshStandardMaterial color="#DCE6D5" />
      </mesh>
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, 0.03, 0]}
        receiveShadow
      >
        <planeGeometry args={[36, 2.4]} />
        <meshStandardMaterial color="#D9D2C0" />
      </mesh>

      <Orchard />
      <SceneContent
        batchCode={batchCode}
        batchStation={batchStation}
        stationStatuses={stationStatuses}
        packagingImageUrl={packagingImageUrl}
        marketingTitle={marketingTitle}
        traceCode={traceCode}
        traced={traced}
        onSelectBatch={onSelectBatch}
        onSelectStation={onSelectStation}
        onOpenTrace={onOpenTrace}
      />

      <OrbitControls
        makeDefault
        enablePan
        enableDamping
        dampingFactor={0.08}
        minPolarAngle={Math.PI / 4.4}
        maxPolarAngle={Math.PI / 3.1}
        minZoom={0.6}
        maxZoom={2.5}
        target={[0, 0, 0]}
      />
    </Canvas>
  );
}
