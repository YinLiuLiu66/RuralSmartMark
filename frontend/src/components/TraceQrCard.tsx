// 工作台里的溯源演示二维码（M5，decisions #30）：跟随当前 origin，不硬编码 localhost。

import { QRCodeSVG } from 'qrcode.react'

import { DEMO_TRACE_CODE, tracePageUrl } from '../api/trace'
import './TraceQrCard.css'

export default function TraceQrCard({ onClose }: { onClose: () => void }) {
  const url = tracePageUrl(DEMO_TRACE_CODE)
  const isLocal = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]'].includes(
    window.location.hostname,
  )

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="modal trace-qr-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <h2>溯源演示</h2>
        <p className="modal-note">
          批次 MJ-DEMO-001 · 固定演示码 {DEMO_TRACE_CODE}
        </p>
        <div className="trace-qr-body">
          <div className="trace-qr-code">
            <QRCodeSVG
              value={url}
              size={148}
              level="M"
              bgColor="#ffffff"
              fgColor="#0b1120"
            />
          </div>
          <div className="trace-qr-copy">
            <p>手机扫码查看「这盒蓝莓的旅程」。</p>
            <a href={url} target="_blank" rel="noreferrer">
              在浏览器打开溯源页
            </a>
            <code>{url}</code>
            {isLocal && (
              <p className="trace-qr-note">
                当前是 localhost，手机扫不到。用 <code>pnpm dev --host</code>{' '}
                启动，并用电脑局域网地址打开本页。
              </p>
            )}
          </div>
        </div>
        <div className="modal-actions">
          <button type="button" className="ghost" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    </div>
  )
}
