import { useEffect, useState, type ReactNode } from "react";
import {
  BadgePercent,
  BookOpen,
  ChevronDown,
  Megaphone,
  Play,
  QrCode,
  Settings,
} from "lucide-react";

import { api, type Batch, type Product } from "../api/client";
import { useWorldStore } from "../stores/world";
import { Scene } from "../three/Scene";
import { STATIONS } from "../three/stations";

const STAGES = [
  { key: "intake", label: "原料入库" },
  { key: "story", label: "故事 IP" },
  { key: "packaging", label: "包装设计" },
  { key: "marketing", label: "内容营销" },
  { key: "pricing", label: "定价上架" },
  { key: "trace", label: "扫码溯源" },
];

const STATE_STAGE: Record<string, number> = {
  raw: 0,
  story_running: 1,
  story_review: 1,
  story_approved: 1,
  packaging_running: 2,
  packaging_review: 2,
  packaging_approved: 2,
  marketing_running: 3,
  marketing_review: 3,
  marketing_approved: 3,
  pricing_running: 4,
  pricing_review: 4,
  pricing_approved: 4,
  traced: 5,
  shipped: 5,
};

const STATUS_LABEL: Record<string, string> = {
  raw: "原料待处理",
  story_running: "故事生成中",
  story_review: "故事待审核",
  story_approved: "故事已定稿",
  packaging_running: "包装生成中",
  packaging_review: "包装待审核",
  packaging_approved: "包装已定稿",
  marketing_running: "内容生成中",
  marketing_review: "内容待审核",
  marketing_approved: "内容已定稿",
  pricing_running: "定价测算中",
  pricing_review: "定价待审核",
  pricing_approved: "定价已定稿",
  traced: "已溯源",
  shipped: "已出库",
};

function Metric({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <div className="card p-3">
      <div className="flex items-center gap-1.5 text-[11px] text-ink-muted">
        {icon}
        {label}
      </div>
      <div className="mt-2 text-lg font-medium text-ink">{value}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/70 pb-2 last:border-0 last:pb-0">
      <span className="text-ink-muted">{label}</span>
      <span className="max-w-[200px] truncate text-right text-ink">{value}</span>
    </div>
  );
}

function stageOf(batch: Batch | null): number {
  return STATE_STAGE[batch?.state ?? ""] ?? 0;
}

export default function Sandbox() {
  const [health, setHealth] = useState<"checking" | "ok" | "error">("checking");
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { batches, selectedBatchId, setBatches, selectBatch } = useWorldStore();

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.health(), api.products(), api.batches()])
      .then(([healthResult, products, batchList]) => {
        if (cancelled) return;
        setHealth(healthResult.status === "ok" ? "ok" : "error");
        setProduct(products[0] ?? null);
        setBatches(batchList);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setHealth("error");
        setError(reason instanceof Error ? reason.message : "加载失败");
      });
    return () => {
      cancelled = true;
    };
  }, [setBatches]);

  const selectedBatch =
    batches.find((batch) => batch.id === selectedBatchId) ?? batches[0] ?? null;
  const stageIndex = stageOf(selectedBatch);
  const statusLabel = selectedBatch
    ? (STATUS_LABEL[selectedBatch.state] ?? selectedBatch.state)
    : "无批次";
  const progress = selectedBatch ? stageIndex + 1 : 0;

  return (
    <>
      <div className="desktop-only min-h-dvh items-center justify-center bg-paper p-6 text-center">
        <div className="max-w-sm">
          <div className="font-display text-2xl text-ink">乡土印记</div>
          <p className="mt-3 text-sm leading-7 text-ink-muted">
            3D 沙盘需要桌面端（≥1024px）。手机请扫描包装上的二维码，打开溯源页。
          </p>
        </div>
      </div>

      <div className="shell">
      <header className="flex items-center gap-4 border-b border-line bg-surface/85 px-5 backdrop-blur">
        <div className="flex items-baseline gap-2">
          <span className="font-display text-xl tracking-wide text-ink">乡土印记</span>
          <span className="text-[11px] text-ink-muted">v2 · 昭通丑苹果</span>
        </div>

        <label className="ml-4 flex items-center gap-2 rounded-control border border-line bg-paper px-3 py-2 text-xs text-ink-muted">
          <span>批次</span>
          <select
            value={selectedBatch?.id ?? ""}
            onChange={(event) => selectBatch(Number(event.target.value) || null)}
            className="max-w-[180px] bg-transparent text-ink outline-none"
          >
            {batches.length === 0 && <option value="">暂无批次</option>}
            {batches.map((batch) => (
              <option key={batch.id} value={batch.id}>
                {batch.code}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </label>

        <div className="ml-auto flex items-center gap-2">
          <span
            className={`rounded-full px-3 py-1 text-[11px] ${
              health === "ok"
                ? "bg-leaf-weak text-leaf"
                : health === "error"
                  ? "bg-apple-weak text-apple"
                  : "bg-surface-2 text-ink-muted"
            }`}
          >
            {health === "ok"
              ? "数据已连接"
              : health === "error"
                ? "后端未连接"
                : "连接中"}
          </span>
          <button
            className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white opacity-60"
            disabled
            title="Phase 1 接入"
          >
            <Play size={14} />
            运行流水线
          </button>
          <button
            className="flex h-8 w-8 items-center justify-center rounded-control border border-line text-ink-muted"
            title="Phase 0 设置未接入"
          >
            <Settings size={16} />
          </button>
        </div>
      </header>

      <div className="shell-main">
        <aside className="border-r border-line bg-paper/70 p-4">
          <section className="card p-4">
            <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-ink-muted">
              <span>品牌护照</span>
              <span className="rounded-full bg-apple-weak px-2 py-0.5 text-[10px] normal-case tracking-normal text-apple">
                演示
              </span>
            </div>
            <div className="mt-3 flex items-end gap-2">
              <span className="font-display text-[40px] leading-none text-ink">
                {progress}/6
              </span>
              <span className="pb-1 text-xs text-ink-muted">
                {STAGES[stageIndex].label}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-6 gap-1">
              {STAGES.map((stage, index) => (
                <div
                  key={stage.key}
                  className={`h-1.5 rounded-full ${
                    index <= stageIndex ? "bg-apple" : "bg-line"
                  }`}
                />
              ))}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-ink-muted">
              {selectedBatch
                ? `${selectedBatch.code} · ${selectedBatch.quantity_kg} kg`
                : "还没有批次"}
            </p>
          </section>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <Metric label="溢价率" value="待测算" icon={<BadgePercent size={14} />} />
            <Metric label="故事" value="待生成" icon={<BookOpen size={14} />} />
            <Metric label="内容素材" value="0" icon={<Megaphone size={14} />} />
            <Metric label="扫码" value="0" icon={<QrCode size={14} />} />
          </div>

          <div className="mt-4 rounded-card border border-dashed border-line p-3 text-[11px] leading-relaxed text-ink-muted">
            Phase 0 数据层已接通。四站点、审核和产出物在 Phase 1–2 接入。
          </div>
        </aside>

        <main className="relative min-h-0 bg-paper">
          <Scene
            batchCode={selectedBatch?.code ?? "ZT-2026-001"}
            onSelectBatch={
              selectedBatch ? () => selectBatch(selectedBatch.id) : undefined
            }
          />
          <div className="pointer-events-none absolute left-5 top-5">
            <div className="rounded-full border border-line bg-surface/90 px-3 py-1 text-[11px] text-ink-muted shadow-card">
              昭通丑苹果 · {selectedBatch?.code ?? "无批次"}
            </div>
          </div>
          {health === "error" && (
            <div className="absolute left-1/2 top-4 -translate-x-1/2 rounded-control border border-danger/30 bg-surface px-4 py-2 text-xs text-danger shadow-card">
              后端未连接：{error ?? "请确认 uvicorn 与 SQLite"}
            </div>
          )}
        </main>

        <aside className="right-rail border-l border-line bg-surface/60 p-4">
          <section className="card p-4">
            <div className="flex items-center justify-between">
              <span className="text-[11px] uppercase tracking-[0.18em] text-ink-muted">
                当前批次
              </span>
              <span className="rounded-full border border-line px-2 py-0.5 text-[10px] text-ink-muted">
                {statusLabel}
              </span>
            </div>
            <h2 className="mt-3 font-display text-2xl text-ink">
              {selectedBatch?.code ?? "还没有批次"}
            </h2>
            <p className="mt-1 text-xs text-ink-muted">
              {product?.name ?? "昭通丑苹果"} · {product?.form ?? "5kg / 12 枚礼盒"}
            </p>

            <div className="mt-4 space-y-2 text-xs">
              <Row
                label="数量"
                value={selectedBatch ? `${selectedBatch.quantity_kg} kg` : "—"}
              />
              <Row
                label="当前站点"
                value={selectedBatch?.current_station ?? "—"}
              />
              <Row
                label="溯源码"
                value={selectedBatch?.trace_code ?? "待生成"}
              />
              <Row label="产品档案" value={product?.slug ?? "—"} />
            </div>

            <button
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white opacity-60"
              disabled
              title="Phase 1 接入"
            >
              <Play size={14} />
              运行流水线
            </button>
          </section>

          <section className="card mt-4 p-4">
            <div className="text-[11px] uppercase tracking-[0.18em] text-ink-muted">
              四站点
            </div>
            <div className="mt-3 space-y-2">
              {STATIONS.map((station) => (
                <div
                  key={station.id}
                  className="flex items-center justify-between rounded-control bg-paper px-3 py-2 text-xs"
                >
                  <span className="flex items-center gap-2 text-ink">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: station.color }}
                    />
                    {station.name}
                  </span>
                  <span className="text-ink-muted">待接入</span>
                </div>
              ))}
            </div>
          </section>
        </aside>
      </div>

      <footer className="border-t border-line bg-surface/85 px-4">
        <div className="grid h-full grid-cols-[minmax(0,1fr)_360px] items-center gap-4">
          <div className="flex items-center gap-2 overflow-x-auto">
            {STAGES.map((stage, index) => (
              <div key={stage.key} className="flex min-w-0 flex-1 items-center gap-2">
                <span
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] ${
                    index < stageIndex
                      ? "bg-leaf text-white"
                      : index === stageIndex
                        ? "bg-apple text-white"
                        : "border border-line text-ink-muted"
                  }`}
                >
                  {index + 1}
                </span>
                <span
                  className={`truncate text-[11px] ${
                    index <= stageIndex ? "text-ink" : "text-ink-muted"
                  }`}
                >
                  {stage.label}
                </span>
                {index < STAGES.length - 1 && <span className="h-px flex-1 bg-line" />}
              </div>
            ))}
          </div>
          <div className="flex gap-1 overflow-x-auto">
            {["故事", "包装", "内容", "定价", "溯源"].map((tab) => (
              <button
                key={tab}
                className="rounded-full border border-line px-3 py-1.5 text-[11px] text-ink-muted"
                disabled
              >
                {tab} 0
              </button>
            ))}
          </div>
        </div>
      </footer>
      </div>
    </>
  );
}
