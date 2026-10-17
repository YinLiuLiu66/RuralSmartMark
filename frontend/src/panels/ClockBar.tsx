// 模拟时钟控制条（decisions #17）：时钟显示 + operator 专属控制按钮。
// JWT 经 client.saveToken 存 localStorage；未登录只显示时钟，不显示登录表单
// （登录 UI 随 M4 工作台一起做）。

import { useState } from 'react'

import { simControl } from '../api/client'
import { useWorld } from '../stores/world'

const SPEED_OPTIONS = [1, 2, 4, 8]

export default function ClockBar() {
  const clock = useWorld((s) => s.clock)
  const reload = useWorld((s) => s.reload)
  const [error, setError] = useState<string | null>(null)
  const [hasToken] = useState(() => localStorage.getItem('rsm_jwt') != null)

  const run = async (action: string, speed?: number) => {
    setError(null)
    try {
      await simControl(action, speed)
      if (action === 'reset') await reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : '控制失败')
    }
  }

  const simDate = clock?.sim_time ? new Date(clock.sim_time) : null
  const timeText = simDate
    ? simDate.toLocaleTimeString('zh-CN', { hour12: false })
    : '--:--:--'

  return (
    <div className="clock-bar">
      <span className="clock-badge">
        <b>{timeText}</b>
        <i>{clock?.running ? '▶ 运行中' : '⏸ 已暂停'}</i>
        <em>{clock ? `${clock.speed}×` : '—'}</em>
      </span>
      <span className="clock-note">模拟时间</span>
      {hasToken && (
        <span className="clock-controls">
          <button type="button" onClick={() => void run(clock?.running ? 'pause' : 'resume')}>
            {clock?.running ? '暂停' : '继续'}
          </button>
          {SPEED_OPTIONS.map((sp) => (
            <button
              key={sp}
              type="button"
              className={clock?.speed === sp ? 'active' : ''}
              onClick={() => void run('speed', sp)}
            >
              {sp}×
            </button>
          ))}
          <button type="button" className="danger" onClick={() => void run('reset')}>
            重置
          </button>
        </span>
      )}
      {error && <span className="clock-error">{error}</span>}
    </div>
  )
}
