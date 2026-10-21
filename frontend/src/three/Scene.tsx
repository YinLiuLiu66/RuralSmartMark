import { Html, OrbitControls, RoundedBox } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useEffect, useState } from "react";

import { STATIONS, type StationMeta, type Vec3 } from "./stations";

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

function StationBuilding({ station }: { station: StationMeta }) {
  return (
    <group position={station.position}>
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
      <Html
        position={[0, 2.95, 0]}
        center
        style={{ pointerEvents: "none" }}
      >
        <div className="whitespace-nowrap rounded-full border border-line bg-surface/95 px-3 py-1 text-[11px] font-medium text-ink shadow-card">
          {station.name}
        </div>
      </Html>
    </group>
  );
}

function BatchPallet({ code, onClick }: { code: string; onClick?: () => void }) {
  return (
    <group position={[-3, 0, -4]} onClick={onClick}>
      <mesh position={[0, 0.12, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.4, 0.24, 1.0]} />
        <meshStandardMaterial color="#C9A46A" />
      </mesh>
      <mesh position={[0, 0.55, 0]} castShadow>
        <boxGeometry args={[1.0, 0.7, 0.8]} />
        <meshStandardMaterial color="#E7D8BF" />
      </mesh>
      <Html
        position={[0, 1.25, 0]}
        center
        style={{ pointerEvents: "none" }}
      >
        <div className="whitespace-nowrap rounded-full border border-apple/30 bg-apple-weak px-3 py-1 text-[11px] font-medium text-apple shadow-card">
          {code} · 原料
        </div>
      </Html>
    </group>
  );
}

function Truck() {
  return (
    <group position={[10, 0, 7.4]}>
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

function Stations() {
  return (
    <>
      {STATIONS.map((station) => (
        <StationBuilding key={station.id} station={station} />
      ))}
    </>
  );
}

function SceneContent({
  batchCode,
  onSelectBatch,
}: {
  batchCode: string;
  onSelectBatch?: () => void;
}) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  if (!ready) return null;

  return (
    <>
      <Stations />
      <BatchPallet code={batchCode} onClick={onSelectBatch} />
      <Truck />
    </>
  );
}

export function Scene({
  batchCode,
  onSelectBatch,
}: {
  batchCode: string;
  onSelectBatch?: () => void;
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
      <SceneContent batchCode={batchCode} onSelectBatch={onSelectBatch} />

      <OrbitControls
        makeDefault
        enablePan
        minPolarAngle={Math.PI / 4.4}
        maxPolarAngle={Math.PI / 3.1}
        minZoom={0.6}
        maxZoom={2.5}
        target={[0, 0, 0]}
      />
    </Canvas>
  );
}
