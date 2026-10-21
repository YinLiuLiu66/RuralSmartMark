// 沙盘右下角的可折叠溢价对照卡（M6，decisions #31）。
// 纯 CSS 条形图，不引 ECharts；数据为演示测算，口径见 API note。

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchPricing } from '../api/pricing'
import './PricingCard.css'

export default function PricingCard() {
  const [open, setOpen] = useState(false)
  const query = useQuery({
    queryKey: ['pricing-benchmarks'],
    queryFn: fetchPricing,
    retry: 1,
  })

  const items = query.data?.items ?? []
  const max = Math.max(...items.map((item) => item.brand_price), 1)

  return (
    <section className={open ? 'pricing-card open' : 'pricing-card'}>
      <button
        type="button"
        className="pricing-toggle"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span>溢价对照</span>
        <span className="pricing-toggle-hint">{open ? '收起' : '展开'}</span>
      </button>

      {open && (
        <div className="pricing-panel">
          <header>
            <h2>礼盒溢价</h2>
            <span>演示测算</span>
          </header>

          {query.isLoading && <p className="pricing-state">溢价数据加载中…</p>}
          {query.isError && <p className="pricing-state">溢价数据加载失败</p>}
          {!query.isLoading && !query.isError && items.length === 0 && (
            <p className="pricing-state">暂无溢价数据</p>
          )}

          {items.map((item) => (
            <div className="pricing-row" key={item.channel}>
              <div className="pricing-row-head">
                <span>{item.channel}</span>
                <strong>+{Math.round(item.premium_rate * 100)}%</strong>
              </div>
              <div className="pricing-bar-row">
                <span className="pricing-bar-tag">散装</span>
                <div className="pricing-track">
                  <div
                    className="pricing-fill bulk"
                    style={{ width: `${(item.bulk_price / max) * 100}%` }}
                  />
                </div>
                <span className="pricing-bar-value">
                  ¥{item.bulk_price.toFixed(0)}
                </span>
              </div>
              <div className="pricing-bar-row">
                <span className="pricing-bar-tag">礼盒</span>
                <div className="pricing-track">
                  <div
                    className="pricing-fill brand"
                    style={{ width: `${(item.brand_price / max) * 100}%` }}
                  />
                </div>
                <span className="pricing-bar-value">
                  ¥{item.brand_price.toFixed(0)}
                </span>
              </div>
            </div>
          ))}

          {query.data && <p className="pricing-note">{query.data.note}</p>}
        </div>
      )}
    </section>
  )
}
