import { lazy, Suspense, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BadgePercent,
  BookOpen,
  Megaphone,
  Play,
  Plus,
  QrCode,
  Settings,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

import {
  AGENTS,
  AGENT_BY_KEY,
  agentStatus,
  nextAgent,
  reviewAgent,
  RUN_STATUS_LABEL,
  RUN_STATUS_STYLE,
  STATE_STAGE,
  STATUS_LABEL,
  type StationStatus,
} from "../agents";
import { api, type KnowledgeDoc } from "../api/client";
import { traceApi } from "../api/trace";
import ControllerPanel from "../components/ControllerPanel";
import ReviewDialog from "../components/ReviewDialog";
import StationCard from "../components/StationCard";
import { usePipelineStore } from "../stores/pipeline";
import { useWorldStore } from "../stores/world";
import { SceneBoundary } from "../three/SceneBoundary";

const Scene = lazy(() =>
  import("../three/Scene").then((module) => ({ default: module.Scene })),
);

const STAGES = [
  { key: "intake", label: "原料入库" },
  { key: "story", label: "故事 IP" },
  { key: "packaging", label: "包装设计" },
  { key: "marketing", label: "内容营销" },
  { key: "pricing", label: "定价上架" },
  { key: "trace", label: "扫码溯源" },
];

function SceneLoading() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-paper">
      <div className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-line border-t-apple" />
        <p className="mt-3 text-xs text-ink-muted">正在搭建沙盘…</p>
      </div>
    </div>
  );
}

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

export default function Sandbox() {
  const [health, setHealth] = useState<"checking" | "ok" | "error">("checking");
  const [sse, setSse] = useState<"connecting" | "live" | "reconnecting">("connecting");
  const [knowledge, setKnowledge] = useState<Record<string, KnowledgeDoc>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [scanCount, setScanCount] = useState(0);
  const [creating, setCreating] = useState(false);
  const [controllerOpen, setControllerOpen] = useState(false);
  const [controllerFreshToken, setControllerFreshToken] = useState<number | undefined>(
    undefined,
  );

  const {
    products,
    selectedProductId,
    batches,
    selectedBatchId,
    setProducts,
    selectProduct,
    setBatches,
    selectBatch,
  } = useWorldStore();
  const {
    workspace,
    selectedAgent,
    packagingVariant,
    setPackagingVariant,
    busy,
    error: pipelineError,
    refresh,
    start,
    run,
    approve,
    reject,
    selectAgent,
  } = usePipelineStore();

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.health(), api.products(), api.batches()])
      .then(([healthResult, productList, batchList]) => {
        if (cancelled) return;
        setHealth(healthResult.status === "ok" ? "ok" : "error");
        setProducts(productList);
        setBatches(batchList);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setHealth("error");
        setLoadError(reason instanceof Error ? reason.message : "加载失败");
      });
    return () => {
      cancelled = true;
    };
  }, [setBatches, setProducts]);

  const selectedProduct =
    products.find((item) => item.id === selectedProductId) ?? products[0] ?? null;

  useEffect(() => {
    if (!selectedProduct) {
      setKnowledge({});
      return;
    }
    let cancelled = false;
    api
      .knowledge(selectedProduct.slug)
      .then((docs) => {
        if (!cancelled) {
          setKnowledge(Object.fromEntries(docs.map((doc) => [doc.doc_key, doc])));
        }
      })
      .catch(() => {
        if (!cancelled) setKnowledge({});
      });
    return () => {
      cancelled = true;
    };
  }, [selectedProduct]);

  useEffect(() => {
    if (!selectedProductId) return;
    const visible = batches.filter((batch) => batch.product_id === selectedProductId);
    if (!visible.some((batch) => batch.id === selectedBatchId)) {
      selectBatch(visible[0]?.id ?? null);
    }
  }, [batches, selectedBatchId, selectedProductId, selectBatch]);

  useEffect(() => {
    if (!selectedBatchId) return;
    selectAgent(null);
    setReviewOpen(false);
    setPackagingVariant("kraft");
    void refresh(selectedBatchId);
  }, [selectedBatchId, refresh, selectAgent, setPackagingVariant]);

  useEffect(() => {
    if (!selectedBatchId) return;
    setSse("connecting");
    const source = new EventSource(`/api/batches/${selectedBatchId}/events`);

    source.onopen = () => setSse("live");
    source.onerror = () => setSse("reconnecting");
    source.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data) as { type?: string; scan_count?: number };
        if (payload.type === "connected") {
          setSse("live");
          void refresh(selectedBatchId, true);
          return;
        }
        if (payload.type === "trace.scanned" && typeof payload.scan_count === "number") {
          setScanCount(payload.scan_count);
        }
        void refresh(selectedBatchId, true);
      } catch {
        // malformed event is ignored; next event will refresh
      }
    };

    return () => source.close();
  }, [selectedBatchId, refresh]);

  const visibleBatches = selectedProductId
    ? batches.filter((batch) => batch.product_id === selectedProductId)
    : batches;
  const selectedBatch =
    visibleBatches.find((batch) => batch.id === selectedBatchId) ??
    visibleBatches[0] ??
    null;
  const currentBatch = workspace?.batch ?? selectedBatch;
  const stageIndex = STATE_STAGE[currentBatch?.state ?? ""] ?? 0;
  const statusLabel = currentBatch
    ? (STATUS_LABEL[currentBatch.state] ?? currentBatch.state)
    : "无批次";
  const next = nextAgent(currentBatch?.state ?? "");
  const review = reviewAgent(currentBatch?.state ?? "");
  const reviewRun =
    workspace?.runs.find(
      (runItem) => runItem.agent === review && runItem.status === "waiting_review",
    ) ?? null;
  const canReview = Boolean(review && reviewRun);
  const reviewMeta = review ? AGENT_BY_KEY[review] : null;
  const selectedMeta = selectedAgent ? AGENT_BY_KEY[selectedAgent] : null;
  const traceCode = currentBatch?.trace_code ?? null;
  const traced = currentBatch?.state === "traced";
  const packagingImageUrl =
    currentBatch && workspace?.batch.packaging_json
      ? traceCode
        ? `/api/trace/${traceCode}/packaging.png?variant=${encodeURIComponent(packagingVariant)}`
        : `/api/batches/${currentBatch.id}/agents/packaging/preview?v=${encodeURIComponent(
            currentBatch.updated_at,
          )}&variant=${encodeURIComponent(packagingVariant)}`
      : null;
  const marketingJson = workspace?.batch.marketing_json as
    | { xiaohongshu?: { title?: string } }
    | null;
  const marketingTitle = marketingJson?.xiaohongshu?.title ?? null;

  useEffect(() => {
    if (!traceCode) {
      setScanCount(0);
      return;
    }
    let cancelled = false;
    traceApi
      .scanCount(traceCode)
      .then((result) => {
        if (!cancelled) setScanCount(result.scan_count);
      })
      .catch(() => {
        if (!cancelled) setScanCount(0);
      });
    return () => {
      cancelled = true;
    };
  }, [traceCode]);

  const stationStatuses = useMemo(() => {
    const result: Record<string, StationStatus> = {};
    for (const agent of AGENTS) {
      result[agent.stationId] = agentStatus(workspace, agent.key);
    }
    return result;
  }, [workspace]);

  const pricing = workspace?.batch.pricing_json as { premium_pct?: number } | null;
  const premiumText =
    typeof pricing?.premium_pct === "number" ? `${pricing.premium_pct}%` : "待测算";
  const story = workspace?.batch.story_json as { ip_name?: string } | null;
  const storyText = story?.ip_name ?? "待生成";
  const contentCount =
    workspace?.runs.some((runItem) => runItem.agent === "marketing" && runItem.output_json)
      ? 1
      : 0;
  const progress = currentBatch ? stageIndex + 1 : 0;
  const nextLabel = next ? AGENT_BY_KEY[next].name : "—";
  const headerLabel = canReview
    ? "审核当前产出"
    : currentBatch?.state === "traced"
      ? "已完成"
      : busy
        ? "运行中…"
        : "运行流水线";
  const headerDisabled =
    !currentBatch ||
    busy ||
    currentBatch.state === "traced" ||
    (!canReview && !next);

  function handleHeader() {
    if (!currentBatch) return;
    if (canReview && review) {
      selectAgent(review);
      setReviewOpen(true);
      return;
    }
    if (next) void start(currentBatch.id);
  }

  async function handleApprove(output: Record<string, unknown>) {
    if (!currentBatch || !review) return;
    const updated = await approve(currentBatch.id, review, output);
    setReviewOpen(false);
    if (updated && updated.batch.state !== "traced") {
      const upcoming = nextAgent(updated.batch.state);
      if (upcoming) {
        const nextWorkspace = await start(updated.batch.id);
        const nextReview = nextWorkspace ? reviewAgent(nextWorkspace.batch.state) : null;
        if (nextReview) selectAgent(nextReview);
      }
    }
  }

  async function handleReject(note: string) {
    if (!currentBatch || !review) return;
    await reject(currentBatch.id, review, note);
    setReviewOpen(false);
  }

  function handleRunAgent() {
    if (!currentBatch || !selectedAgent) return;
    void run(currentBatch.id, selectedAgent);
  }

  function handleSelectStation(stationId: string) {
    const agent = AGENTS.find((item) => item.stationId === stationId);
    if (agent) selectAgent(agent.key);
  }

  function handleOpenTrace() {
    if (!traceCode) return;
    window.open(`/trace/${traceCode}`, "_blank", "noopener,noreferrer");
  }

  async function handleCreateBatch() {
    setCreating(true);
    setLoadError(null);
    try {
      const batch = await api.createBatch(selectedProduct?.slug);
      setBatches([batch, ...batches]);
      selectBatch(batch.id);
    } catch (reason: unknown) {
      setLoadError(reason instanceof Error ? reason.message : "新建批次失败");
    } finally {
      setCreating(false);
    }
  }

  async function handleControllerDataChanged() {
    const [productList, batchList] = await Promise.all([api.products(), api.batches()]);
    const newest = productList[productList.length - 1] ?? null;
    setProducts(productList);
    setBatches(batchList);
    if (newest && !products.some((item) => item.id === newest.id)) {
      selectProduct(newest.id);
      const visible = batchList.filter((batch) => batch.product_id === newest.id);
      selectBatch(visible[0]?.id ?? null);
    }
  }

  return (
    <>
      <div className="desktop-only min-h-dvh items-center justify-center bg-paper p-6 text-center">
        <div className="max-w-sm">
          <div className="font-display text-2xl text-ink">智农云链</div>
          <p className="mt-3 text-sm leading-7 text-ink-muted">
            3D 沙盘需要桌面端（≥1024px）。手机请扫描包装上的二维码，打开溯源页。
          </p>
        </div>
      </div>

      <div className="shell">
        <header className="flex items-center gap-4 border-b border-line bg-surface/85 px-5 backdrop-blur">
          <div className="flex items-baseline gap-2">
            <span className="font-display text-xl tracking-wide text-ink">智农云链</span>
            <span className="text-[11px] text-ink-muted">
              多智能体 · {selectedProduct?.name ?? "未选择产品"}
            </span>
          </div>

          <label className="ml-4 flex items-center gap-2 rounded-control border border-line bg-paper px-3 py-2 text-xs text-ink-muted">
            <span>产品</span>
            <select
              value={selectedProduct?.id ?? ""}
              onChange={(event) => selectProduct(Number(event.target.value) || null)}
              className="max-w-[160px] bg-transparent text-ink outline-none"
            >
              {products.length === 0 && <option value="">暂无产品</option>}
              {products.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            aria-label="新建产品"
            title="新建产品"
            onClick={() => {
              setControllerFreshToken(Date.now());
              setControllerOpen(true);
            }}
            className="flex h-9 w-9 items-center justify-center rounded-control border border-line bg-surface text-ink-muted hover:border-apple/40 hover:text-apple"
          >
            <Plus size={15} />
          </button>

          <label className="flex items-center gap-2 rounded-control border border-line bg-paper px-3 py-2 text-xs text-ink-muted">
            <span>批次</span>
            <select
              value={selectedBatch?.id ?? ""}
              onChange={(event) => selectBatch(Number(event.target.value) || null)}
              className="max-w-[180px] bg-transparent text-ink outline-none"
            >
              {visibleBatches.length === 0 && <option value="">暂无批次</option>}
              {visibleBatches.map((batch) => (
                <option key={batch.id} value={batch.id}>
                  {batch.code}
                </option>
              ))}
            </select>
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
              {health === "ok" ? "数据已连接" : health === "error" ? "后端未连接" : "连接中"}
            </span>
            <span
              className={`rounded-full px-3 py-1 text-[11px] ${
                sse === "live"
                  ? "bg-leaf-weak text-leaf"
                  : sse === "reconnecting"
                    ? "bg-amber/10 text-amber"
                    : "bg-surface-2 text-ink-muted"
              }`}
            >
              {sse === "live" ? "实时" : sse === "reconnecting" ? "重连中" : "订阅中"}
            </span>
            <button
              type="button"
              aria-label="打开总控"
              onClick={() => {
                setControllerFreshToken(undefined);
                setControllerOpen(true);
              }}
              className="flex items-center gap-1.5 rounded-control border border-line bg-surface px-3 py-2 text-xs text-ink-muted hover:border-apple/40 hover:text-apple"
            >
              <Sparkles size={14} />
              总控
            </button>
            <button
              className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
              onClick={handleHeader}
              disabled={headerDisabled}
            >
              {canReview ? <ShieldCheck size={14} /> : <Play size={14} />}
              {headerLabel}
            </button>
            <button
              className="flex h-8 w-8 items-center justify-center rounded-control border border-line text-ink-muted"
              title="设置（暂未接入）"
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
                {currentBatch
                  ? `${currentBatch.code} · ${currentBatch.quantity_kg} kg · ${statusLabel}`
                  : "还没有批次"}
              </p>
            </section>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="溢价率（演示）" value={premiumText} icon={<BadgePercent size={14} />} />
              <Metric label="故事" value={storyText} icon={<BookOpen size={14} />} />
              <Metric
                label="内容素材"
                value={`${contentCount} 条`}
                icon={<Megaphone size={14} />}
              />
              <Metric
                label="扫码（累计）"
                value={`${scanCount} 次`}
                icon={<QrCode size={14} />}
              />
            </div>

            <div className="mt-4 rounded-card border border-dashed border-line p-3 text-[11px] leading-relaxed text-ink-muted">
              四站产出均经人工审核。点站点查看故事、包装、内容与定价；扫码可打开这一批的手机溯源页。
            </div>
          </aside>

          <main className="relative min-h-0 bg-paper">
            <SceneBoundary>
              <Suspense fallback={<SceneLoading />}>
                <Scene
                  batchCode={currentBatch?.code ?? "ZT-2026-001"}
                  batchStation={currentBatch?.current_station ?? "intake"}
                  stationStatuses={stationStatuses}
                  packagingImageUrl={packagingImageUrl}
                  marketingTitle={marketingTitle}
                  traceCode={traceCode}
                  traced={traced}
                  onSelectBatch={() => {
                    if (currentBatch) selectBatch(currentBatch.id);
                  }}
                  onSelectStation={handleSelectStation}
                  onOpenTrace={handleOpenTrace}
                />
              </Suspense>
            </SceneBoundary>
            <div className="pointer-events-none absolute left-5 top-5">
              <div className="rounded-full border border-line bg-surface/90 px-3 py-1 text-[11px] text-ink-muted shadow-card">
                {selectedProduct?.name ?? "未选择产品"} · {currentBatch?.code ?? "无批次"} · {statusLabel}
              </div>
            </div>
            {(loadError || pipelineError) && (
              <div className="absolute left-1/2 top-4 flex max-w-[80%] -translate-x-1/2 items-center gap-2 rounded-control border border-danger/30 bg-surface px-4 py-2 text-xs text-danger shadow-card">
                <span>{loadError ?? pipelineError}</span>
                {loadError && (
                  <button
                    type="button"
                    onClick={() => window.location.reload()}
                    className="shrink-0 underline underline-offset-4"
                  >
                    重试
                  </button>
                )}
              </div>
            )}
          </main>

          <aside className="right-rail overflow-y-auto border-l border-line bg-surface/60 p-4">
            {selectedMeta && workspace ? (
              <StationCard
                agent={selectedMeta}
                workspace={workspace}
                knowledge={knowledge}
                busy={busy}
                onRun={handleRunAgent}
                onReview={() => setReviewOpen(true)}
                onClose={() => selectAgent(null)}
                packagingVariant={packagingVariant}
                onPackagingVariantChange={setPackagingVariant}
              />
            ) : (
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
                  {currentBatch?.code ?? "还没有批次"}
                </h2>
                <p className="mt-1 text-xs text-ink-muted">
                  {selectedProduct?.name ?? "未选择产品"} ·{" "}
                  {selectedProduct?.form ?? "—"}
                </p>

                <div className="mt-4 space-y-2 text-xs">
                  <Row
                    label="数量"
                    value={currentBatch ? `${currentBatch.quantity_kg} kg` : "—"}
                  />
                  <Row
                    label="当前站点"
                    value={currentBatch?.current_station ?? "—"}
                  />
                  <Row
                    label="下一步"
                    value={canReview ? `审核 ${review ? AGENT_BY_KEY[review].name : ""}` : nextLabel}
                  />
                  <Row
                    label="溯源码"
                    value={currentBatch?.trace_code ?? "待生成"}
                  />
                  <Row label="产品档案" value={selectedProduct?.slug ?? "—"} />
                </div>

                <p className="mt-4 text-[11px] leading-relaxed text-ink-muted">
                  点顶栏按钮运行/审核；点 3D 站点或右侧四站点查看每个 Agent 的产出。
                </p>
                {!currentBatch && (
                  <button
                    type="button"
                    onClick={() => void handleCreateBatch()}
                    disabled={creating}
                    className="mt-3 w-full rounded-control bg-apple px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
                  >
                    {creating ? "新建中…" : "新建演示批次"}
                  </button>
                )}
              </section>
            )}

            <section className="card mt-4 p-4">
              <div className="text-[11px] uppercase tracking-[0.18em] text-ink-muted">
                四站点
              </div>
              <div className="mt-3 space-y-2">
                {AGENTS.map((agent) => {
                  const status = stationStatuses[agent.stationId] ?? "idle";
                  const active = selectedAgent === agent.key;
                  return (
                    <button
                      key={agent.key}
                      type="button"
                      onClick={() => selectAgent(agent.key)}
                      aria-pressed={active}
                      title={`查看${agent.name}产出`}
                      className={`flex w-full cursor-pointer items-center justify-between rounded-control border px-3 py-2 text-left text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-apple/30 ${
                        active
                          ? "border-apple/40 bg-apple-weak shadow-[inset_3px_0_0_var(--color-apple)]"
                          : "border-transparent bg-paper hover:border-apple/20 hover:bg-apple-weak/40"
                      }`}
                    >
                      <span className="flex items-center gap-2 text-ink">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: agent.color }}
                        />
                        {agent.name}
                      </span>
                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] ${RUN_STATUS_STYLE[status]}`}
                      >
                        {RUN_STATUS_LABEL[status]}
                      </span>
                    </button>
                  );
                })}
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
              {AGENTS.map((agent) => {
                const count =
                  workspace?.artifacts.filter((artifact) => artifact.kind === agent.key)
                    .length ?? 0;
                return (
                  <button
                    key={agent.key}
                    onClick={() => selectAgent(agent.key)}
                    className={`rounded-full border px-3 py-1.5 text-[11px] ${
                      selectedAgent === agent.key
                        ? "border-apple/30 bg-apple-weak text-apple"
                        : "border-line text-ink-muted"
                    }`}
                  >
                    {agent.short} {count}
                  </button>
                );
              })}
              <Link
                to={`/trace/${traceCode ?? "ZTDEMO26"}`}
                className="rounded-full border border-line px-3 py-1.5 text-[11px] text-ink-muted"
              >
                {traceCode ? "溯源" : "演示溯源"}
              </Link>
            </div>
          </div>
        </footer>

        {reviewMeta && reviewRun && (
          <ReviewDialog
            open={reviewOpen}
            agent={reviewMeta}
            batchId={currentBatch?.id ?? null}
            output={reviewRun.output_json}
            guard={reviewRun.guard_json}
            knowledge={knowledge}
            busy={busy}
            onClose={() => setReviewOpen(false)}
            onApprove={handleApprove}
            onReject={handleReject}
          />
        )}
      </div>

      {controllerOpen && (
        <ControllerPanel
          productSlug={
            controllerFreshToken !== undefined ? null : selectedProduct?.slug ?? null
          }
          batchId={controllerFreshToken !== undefined ? null : selectedBatch?.id ?? null}
          freshToken={controllerFreshToken}
          onNewProduct={() => setControllerFreshToken(Date.now())}
          onClose={() => setControllerOpen(false)}
          onDataChanged={() => void handleControllerDataChanged()}
        />
      )}
    </>
  );
}
