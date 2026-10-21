// 扫码溯源 H5（M5，decisions #30）：公开页，时间线读 trace_event，故事取 Agent 1 定稿。

import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'

import { ApiError } from '../api/client'
import { fetchTrace } from '../api/trace'
import type { TraceEvent, TraceResponse } from '../api/types'
import './Trace.css'

const TIME_RE = /T(\d{2}:\d{2})/

function timeOf(iso: string | null): string {
  return iso?.match(TIME_RE)?.[1] ?? '--:--'
}

function Story({ content }: { content: string }) {
  const lines = content
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
  return (
    <div className="trace-story">
      {lines.map((line, index) => (
        <p key={index} className={line.startsWith('IP 定位') ? 'trace-ip' : undefined}>
          {line}
        </p>
      ))}
    </div>
  )
}

function Event({ event }: { event: TraceEvent }) {
  const alert = event.kind === 'temp_alert'
  return (
    <li className={alert ? 'trace-event alert' : 'trace-event'}>
      <span className="trace-time">{timeOf(event.sim_time)}</span>
      <span className="trace-dot" aria-hidden="true" />
      <div className="trace-event-body">
        <div className="trace-event-head">
          <strong>{event.label}</strong>
          {event.site_name && <span>{event.site_name}</span>}
          {event.vehicle_plate && <span>{event.vehicle_plate}</span>}
        </div>
        {event.note && <p>{event.note}</p>}
        {event.temperature !== null && (
          <p className="trace-temp">车厢温度 {event.temperature.toFixed(1)}℃</p>
        )}
      </div>
    </li>
  )
}

function State({ title, note }: { title: string; note: string }) {
  return (
    <main className="trace-page">
      <div className="trace-state">
        <p className="trace-kicker">麻江蓝莓 · 一物一码</p>
        <h1>{title}</h1>
        <p>{note}</p>
        <a href="/">返回 3D 沙盘</a>
      </div>
    </main>
  )
}

function Content({ trace }: { trace: TraceResponse }) {
  const first = trace.timeline[0]
  const demoDate = first?.sim_time?.slice(0, 10)
  return (
    <main className="trace-page">
      <div className="trace-wrap">
        <header className="trace-hero">
          <p className="trace-kicker">麻江蓝莓 · 一物一码</p>
          <h1>这盒蓝莓的旅程</h1>
          <p className="trace-sub">从麻江的山坡，到凯里门店的礼盒专区。</p>
          <div className="trace-chips">
            {trace.is_demo && <span className="trace-chip demo">演示样张</span>}
            <span className="trace-chip">批次 {trace.product.batch_no}</span>
            <span className="trace-chip">溯源码 {trace.code}</span>
          </div>
        </header>

        <section className="trace-card trace-product">
          <div>
            <span className="trace-label">产品</span>
            <h2>{trace.product.name}</h2>
            <p>
              一托 {trace.product.qty} 盒 · 礼盒定价 ¥{trace.product.box_price.toFixed(0)}
            </p>
          </div>
          <span className="trace-product-mark">{trace.is_demo ? 'DEMO' : 'TRACE'}</span>
        </section>

        {trace.story && (
          <section className="trace-card">
            <div className="trace-card-head">
              <h2>品牌故事</h2>
              <span>Agent 1 定稿</span>
            </div>
            <Story content={trace.story.content} />
          </section>
        )}

        <section className="trace-card">
          <div className="trace-card-head">
            <h2>全程记录</h2>
            <span>{trace.timeline.length} 个节点</span>
          </div>
          <ol className="trace-timeline">
            {trace.timeline.map((event) => (
              <Event key={event.id} event={event} />
            ))}
          </ol>
          {demoDate && (
            <p className="trace-footnote">
              时间线来自模拟沙盘，显示为演示日 {demoDate} 的时间。
            </p>
          )}
        </section>

        <footer className="trace-foot">
          <span>RuralSmartMark · 麻江蓝莓数字孪生供应链</span>
          <a href="/">查看 3D 沙盘</a>
        </footer>
      </div>
    </main>
  )
}

export default function Trace() {
  const raw = useParams().code ?? ''
  const code = raw.toUpperCase()
  const query = useQuery({
    queryKey: ['trace', code],
    queryFn: () => fetchTrace(code),
    enabled: Boolean(code),
    retry: 0,
  })

  if (!code) {
    return <State title="缺少溯源码" note="请从礼盒上的二维码进入。" />
  }
  if (query.isLoading) {
    return <State title="正在读取溯源记录…" note="数据来自麻江蓝莓数字孪生沙盘。" />
  }
  if (query.isError) {
    const notFound = query.error instanceof ApiError && query.error.status === 404
    return (
      <State
        title={notFound ? '没有找到这枚溯源码' : '溯源记录加载失败'}
        note={
          notFound
            ? `码 ${code} 不在演示批次中。`
            : '请稍后重试，或检查后端服务是否在运行。'
        }
      />
    )
  }
  if (!query.data) {
    return <State title="暂无溯源数据" note="该批次还没有写入时间线。" />
  }
  return <Content trace={query.data} />
}
