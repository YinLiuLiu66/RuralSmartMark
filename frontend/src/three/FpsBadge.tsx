import { useEffect, useState } from 'react'

/** rAF 自测帧率，仅供 M0 探针验收用；独立组件避免每秒重渲上层页面 */
export default function FpsBadge() {
  const [fps, setFps] = useState(0)

  useEffect(() => {
    let frames = 0
    let last = performance.now()
    let raf = 0

    const tick = (now: number) => {
      frames += 1
      if (now - last >= 1000) {
        setFps(Math.round((frames * 1000) / (now - last)))
        frames = 0
        last = now
      }
      raf = requestAnimationFrame(tick)
    }

    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  return <span className="fps-badge">帧率 {fps || '—'} fps</span>
}
