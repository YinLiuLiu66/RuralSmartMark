import { useEffect, useState } from 'react'

import { useWorld } from './stores/world'
import ClockBar from './panels/ClockBar'
import DetailCard from './three/DetailCard'
import WorldScene from './three/WorldScene'
import FpsBadge from './three/FpsBadge'
import './App.css'

type SelectedKind = 'site' | 'vehicle' | 'shipment'

function App() {
  const connect = useWorld((s) => s.connect)
  const disconnect = useWorld((s) => s.disconnect)
  const reload = useWorld((s) => s.reload)
  const ready = useWorld((s) => s.ready)
  // 详情卡选中态：站点/车辆在 3D 场景里点，运单只在卡片侧列出可点
  const [selected, setSelected] = useState<{ kind: SelectedKind; id: number } | null>(null)

  useEffect(() => {
    void reload()
    connect()
    return () => disconnect()
  }, [connect, disconnect, reload])

  return (
    <main className="probe">
      <div className="probe-stage">
        <WorldScene
          selectedKind={selected?.kind === 'shipment' ? null : (selected?.kind ?? null)}
          selectedId={selected?.id ?? null}
          onSelect={(kind, id) => setSelected({ kind, id })}
        />

        <header className="probe-head">
          <h1>云岭蓝莓 · 数字孪生供应链沙盘</h1>
          <p>拖动旋转 / 滚轮缩放 / 点击站点或车辆查看实时详情</p>
        </header>

        <ClockBar />

        <DetailCard
          kind={selected?.kind ?? null}
          id={selected?.id ?? null}
          onClose={() => setSelected(null)}
        />

        <FpsBadge />

        <footer className="probe-foot">
          {ready ? '实时同步中' : '连接世界…'} · three 0.169 + fiber 8.17 + drei 9.114
        </footer>
      </div>
    </main>
  )
}

export default App
