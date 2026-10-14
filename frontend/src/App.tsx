import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from './api/client'
import './App.css'

type Status =
  | { kind: 'loading' }
  | { kind: 'ok'; data: HealthResponse }
  | { kind: 'error'; message: string }

function App() {
  const [status, setStatus] = useState<Status>({ kind: 'loading' })

  useEffect(() => {
    let cancelled = false

    fetchHealth()
      .then((data) => {
        if (!cancelled) setStatus({ kind: 'ok', data })
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setStatus({
            kind: 'error',
            message: error instanceof Error ? error.message : '未知错误',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <main className="app">
      <h1>RuralSmartMark</h1>
      <p className="subtitle">前端 React 18 + Vite + TypeScript</p>

      <section className="card">
        <h2>后端连通性</h2>
        {status.kind === 'loading' && <p>检测中…</p>}
        {status.kind === 'ok' && (
          <p className="ok">
            {status.data.service} 状态：{status.data.status}
          </p>
        )}
        {status.kind === 'error' && (
          <p className="error">
            {status.message}（确认后端已在 127.0.0.1:8000 启动）
          </p>
        )}
      </section>
    </main>
  )
}

export default App
