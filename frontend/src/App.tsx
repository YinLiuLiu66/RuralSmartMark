import { useMemo, useState } from 'react'
import ProbeScene from './three/ProbeScene'
import FpsBadge from './three/FpsBadge'
import { SITES } from './three/probeData'
import './App.css'

function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const selected = useMemo(() => SITES.find((s) => s.id === selectedId) ?? null, [selectedId])

  return (
    <main className="probe">
      <div className="probe-stage">
        <ProbeScene selectedId={selectedId} onSelect={setSelectedId} />

        <header className="probe-head">
          <h1>RuralSmartMark · M0 探针</h1>
          <p>程序化 low-poly 等距沙盘：拖动旋转 / 滚轮缩放 / 点击站点查看数据卡</p>
        </header>

        <aside className="probe-card">
          {selected ? (
            <>
              <h2 style={{ color: selected.color }}>{selected.name}</h2>
              <dl>
                <div>
                  <dt>库存</dt>
                  <dd>{selected.info.pallets} 托</dd>
                </div>
                <div>
                  <dt>温区</dt>
                  <dd>{selected.info.tempZone}</dd>
                </div>
                <div>
                  <dt>今日吞吐</dt>
                  <dd>{selected.info.throughput}</dd>
                </div>
                <div>
                  <dt>备注</dt>
                  <dd>{selected.info.note}</dd>
                </div>
              </dl>
              <button type="button" onClick={() => setSelectedId(null)}>
                关闭
              </button>
            </>
          ) : (
            <p className="probe-card-empty">
              点击任一站点方块
              <br />
              查看模拟数据卡
            </p>
          )}
        </aside>

        <FpsBadge />

        <footer className="probe-foot">探针小样 · three 0.169 + fiber 8.17 + drei 9.114</footer>
      </div>
    </main>
  )
}

export default App
