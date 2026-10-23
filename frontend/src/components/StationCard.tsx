import { useEffect, useState } from "react";
import { ArrowLeft, ExternalLink, Play, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";

import {
  pipelineApi,
  type AgentKey,
  type Artifact,
  type BatchWorkspace,
  type PackagingVariant,
} from "../api/pipeline";
import type { KnowledgeDoc } from "../api/client";
import {
  agentStatus,
  latestRun,
  nextAgent,
  outputForAgent,
  RUN_STATUS_LABEL,
  RUN_STATUS_STYLE,
  type AgentMeta,
} from "../agents";

interface Citation {
  doc_id: string;
  quote: string;
  use: string;
}

function citationsOf(output: Record<string, unknown> | null): Citation[] {
  if (!output) return [];
  const raw = output.cultural_evidence ?? output.fact_refs;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (item): item is Citation =>
      Boolean(item) &&
      typeof item === "object" &&
      typeof (item as Citation).doc_id === "string",
  );
}

function GuardPanel({ run }: { run: ReturnType<typeof latestRun> }) {
  const issues = [...(run?.guard_json?.warnings ?? []), ...(run?.guard_json?.errors ?? [])];
  if (issues.length === 0) return null;
  return (
    <div className="mt-3 space-y-1.5">
      {issues.slice(0, 5).map((issue) => (
        <div
          key={`${issue.rule}-${issue.field}-${issue.message}`}
          className={`flex gap-1.5 rounded-control px-2 py-1.5 text-[10.5px] leading-4 ${
            issue.severity === "error"
              ? "bg-apple-weak text-danger"
              : "bg-amber/10 text-amber"
          }`}
          title={issue.suggestion}
        >
          <TriangleAlert size={12} className="mt-0.5 shrink-0" />
          <span className="min-w-0">
            <b className="font-medium">{issue.rule}</b> · {issue.message}
          </span>
        </div>
      ))}
      {issues.length > 5 && (
        <p className="text-[10px] text-ink-muted">还有 {issues.length - 5} 条预警，审核时查看完整 JSON。</p>
      )}
    </div>
  );
}

function Citations({
  output,
  knowledge,
}: {
  output: Record<string, unknown> | null;
  knowledge: Record<string, KnowledgeDoc>;
}) {
  const items = citationsOf(output);
  if (items.length === 0) return null;
  return (
    <div className="mt-3">
      <div className="text-[10px] uppercase tracking-[0.18em] text-ink-muted">
        引用证据 · {items.length}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1.5">
        {items.map((citation, index) => {
          const doc = knowledge[citation.doc_id];
          const demo = doc?.credibility === "demo" || citation.doc_id.startsWith("DEMO");
          const url = doc?.source_url?.startsWith("http") ? doc.source_url : null;
          const label = `${citation.doc_id}${doc ? ` · ${doc.title}` : ""}`;
          const className =
            "inline-flex max-w-full items-center gap-1 rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] text-ink-muted";
          return url ? (
            <a
              key={`${citation.doc_id}-${index}`}
              href={url}
              target="_blank"
              rel="noreferrer"
              className={`${className} hover:border-apple/40 hover:text-apple`}
              title={citation.quote}
            >
              <span className="truncate">{label}</span>
              <ExternalLink size={10} className="shrink-0" />
              {demo && <span className="shrink-0 text-amber">演示</span>}
            </a>
          ) : (
            <span key={`${citation.doc_id}-${index}`} className={className} title={citation.quote}>
              <span className="truncate">{label}</span>
              {demo && <span className="shrink-0 text-amber">演示</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}

function StoryPreview({ output }: { output: Record<string, unknown> }) {
  const taglines = Array.isArray(output.taglines) ? output.taglines : [];
  return (
    <div>
      <div className="font-display text-xl text-ink">{String(output.ip_name ?? "故事")}</div>
      <p className="mt-1 text-xs text-apple">{String(output.story_short ?? "")}</p>
      <p className="mt-2 line-clamp-4 text-[11px] leading-5 text-ink-muted">
        {String(output.story_long ?? "")}
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {taglines.slice(0, 3).map((tagline) => (
          <span key={String(tagline)} className="rounded-full bg-surface-2 px-2 py-0.5 text-[10px] text-ink-muted">
            {String(tagline)}
          </span>
        ))}
      </div>
    </div>
  );
}

function PackagingPreview({
  batchId,
  runId,
  output,
  illustration,
  variants,
  variant,
  onVariantChange,
}: {
  batchId: number;
  runId: number | null;
  output: Record<string, unknown>;
  illustration: Artifact | null;
  variants: PackagingVariant[];
  variant: string;
  onVariantChange: (variant: string) => void;
}) {
  const copy = (output.packaging_copy ?? {}) as Record<string, unknown>;
  const structure = (output.structure ?? {}) as Record<string, unknown>;
  const current = variants.find((item) => item.key === variant);
  const [illustrationFailed, setIllustrationFailed] = useState(false);

  useEffect(() => {
    setIllustrationFailed(false);
  }, [illustration?.file_url]);

  const illustrationError = Boolean(illustration?.content_json?.error) || illustrationFailed;

  return (
    <div>
      {variants.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {variants.map((item) => (
            <button
              key={item.key}
              type="button"
              title={item.description}
              onClick={() => onVariantChange(item.key)}
              className={`flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] transition-colors ${
                item.key === variant
                  ? "border-apple/40 bg-apple-weak text-apple"
                  : "border-line bg-paper text-ink-muted hover:border-apple/30 hover:bg-apple-weak/40 hover:text-apple"
              }`}
            >
              <span className="flex -space-x-1">
                {item.swatches.slice(0, 3).map((color, index) => (
                  <span
                    key={`${item.key}-${index}`}
                    className="h-2.5 w-2.5 rounded-full border border-white"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </span>
              {item.name}
            </button>
          ))}
        </div>
      )}
      <div className="overflow-hidden rounded-control border border-line bg-surface-2">
        <img
          key={`${runId ?? 0}-${variant}`}
          src={`/api/batches/${batchId}/agents/packaging/preview?run=${runId ?? 0}&variant=${variant}`}
          alt="包装示意预览"
          className="aspect-[8/5] w-full object-cover"
        />
      </div>
      <p className="mt-2 text-[10.5px] text-ink-muted">
        服务端渲染 · 审核通过后落 PNG{current ? ` · ${current.description}` : ""}
      </p>
      <div className="mt-2 text-xs font-medium text-ink">{String(output.concept ?? "")}</div>
      <div className="mt-2 grid grid-cols-2 gap-1.5 text-[10.5px] text-ink-muted">
        <span>正面：{String(copy.front ?? "—")}</span>
        <span>侧面：{String(copy.side ?? "—")}</span>
        <span className="col-span-2">盒型：{String(structure.box_type ?? "—")}</span>
      </div>
      {illustration?.file_url && !illustrationError && (
        <div className="mt-3 overflow-hidden rounded-control border border-line bg-surface-2">
          <img
            src={illustration.file_url}
            alt="IP 插画（AI 生成）"
            className="aspect-[3/4] w-full object-cover"
            onError={() => setIllustrationFailed(true)}
          />
          <p className="border-t border-line px-2 py-1.5 text-[10px] text-ink-muted">
            IP 插画 · {String(illustration.content_json?.model ?? "Z-Image-Turbo")} · 演示合成
          </p>
        </div>
      )}
      {illustrationError && (
        <div
          role="status"
          className="mt-3 overflow-hidden rounded-control border border-dashed border-line bg-surface-2"
        >
          <div className="flex aspect-[3/4] flex-col items-center justify-center gap-2 px-5 text-center">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-apple-weak text-[11px] font-medium text-apple">
              IP
            </span>
            <p className="text-xs text-ink">插画这次没有生成</p>
            <p className="text-[10px] leading-5 text-ink-faint">
              包装审核不受影响；可稍后重跑包装。
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

function MarketingPreview({ output }: { output: Record<string, unknown> }) {
  const xhs = (output.xiaohongshu ?? {}) as Record<string, unknown>;
  const douyin = (output.douyin ?? {}) as Record<string, unknown>;
  const tags = Array.isArray(xhs.tags) ? xhs.tags : [];
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-ink-muted">小红书</div>
      <div className="mt-1 text-sm font-medium text-ink">{String(xhs.title ?? "—")}</div>
      <p className="mt-1 line-clamp-3 text-[11px] leading-5 text-ink-muted">
        {String(xhs.body ?? "")}
      </p>
      <div className="mt-1.5 flex flex-wrap gap-1">
        {tags.slice(0, 4).map((tag) => (
          <span key={String(tag)} className="rounded-full bg-leaf-weak px-2 py-0.5 text-[10px] text-leaf">
            {String(tag)}
          </span>
        ))}
      </div>
      <div className="mt-3 border-t border-line pt-2 text-[10px] uppercase tracking-[0.18em] text-ink-muted">
        抖音钩子
      </div>
      <p className="mt-1 line-clamp-2 text-[11px] leading-5 text-ink-muted">
        {String(douyin.hook ?? "—")}
      </p>
    </div>
  );
}

function PricingPreview({ output }: { output: Record<string, unknown> }) {
  const ladder = Array.isArray(output.price_ladder) ? output.price_ladder : [];
  const formula = String(output.formula ?? "");
  return (
    <div>
      <div className="flex items-end gap-2">
        <span className="font-display text-3xl leading-none text-ink">
          {String(output.premium_pct ?? "—")}%
        </span>
        <span className="pb-1 text-[10px] text-ink-muted">相对散装基线</span>
        <span className="mb-0.5 ml-auto rounded-full bg-amber/10 px-2 py-0.5 text-[10px] text-amber">
          演示测算
        </span>
      </div>
      <div className="mt-2 space-y-1">
        {ladder.map((tier) => {
          const row = tier as Record<string, unknown>;
          return (
            <div key={String(row.channel)} className="flex items-baseline justify-between gap-2 text-[11px]">
              <span className="truncate text-ink-muted">{String(row.channel)}</span>
              <span className="shrink-0 font-medium tabular-nums text-ink">
                ¥{String(row.price_total)} / {String(row.pack)}
              </span>
            </div>
          );
        })}
      </div>
      <details className="mt-2 text-[10px] text-ink-muted">
        <summary className="cursor-pointer">溢价公式</summary>
        <p className="mt-1 break-words leading-4">{formula}</p>
      </details>
    </div>
  );
}

function OutputPreview({
  agent,
  batchId,
  runId,
  output,
  illustration,
  variants,
  variant,
  onVariantChange,
}: {
  agent: AgentKey;
  batchId: number;
  runId: number | null;
  output: Record<string, unknown>;
  illustration: Artifact | null;
  variants: PackagingVariant[];
  variant: string;
  onVariantChange: (variant: string) => void;
}) {
  if (agent === "story") return <StoryPreview output={output} />;
  if (agent === "packaging") {
    return (
      <PackagingPreview
        batchId={batchId}
        runId={runId}
        output={output}
        illustration={illustration}
        variants={variants}
        variant={variant}
        onVariantChange={onVariantChange}
      />
    );
  }
  if (agent === "marketing") return <MarketingPreview output={output} />;
  return <PricingPreview output={output} />;
}

export default function StationCard({
  agent,
  workspace,
  knowledge,
  busy,
  onRun,
  onReview,
  onClose,
  packagingVariant,
  onPackagingVariantChange,
}: {
  agent: AgentMeta;
  workspace: BatchWorkspace;
  knowledge: Record<string, KnowledgeDoc>;
  busy: boolean;
  onRun: () => void;
  onReview: () => void;
  onClose: () => void;
  packagingVariant: string;
  onPackagingVariantChange: (variant: string) => void;
}) {
  const [variants, setVariants] = useState<PackagingVariant[]>([]);
  const status = agentStatus(workspace, agent.key);
  const run = latestRun(workspace, agent.key);
  const output = outputForAgent(workspace, agent.key);
  const illustration =
    workspace.artifacts.find((artifact) => artifact.kind === "illustration") ?? null;

  useEffect(() => {
    if (agent.key !== "packaging") return;
    let cancelled = false;
    pipelineApi
      .packagingVariants(workspace.batch.id)
      .then((items) => {
        if (!cancelled) setVariants(items);
      })
      .catch(() => {
        if (!cancelled) setVariants([]);
      });
    return () => {
      cancelled = true;
    };
  }, [agent.key, workspace.batch.id]);
  const canRun =
    nextAgent(workspace.batch.state) === agent.key ||
    workspace.batch.state === `${agent.key}_review`;
  const reviewable = status === "review" && run?.status === "waiting_review";
  const isDemo = output?.demo === true;

  return (
    <section className="card p-4">
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={onClose}
          className="flex items-center gap-1 text-[11px] text-ink-muted hover:text-ink"
        >
          <ArrowLeft size={13} />
          返回批次
        </button>
        <span
          className={`rounded-full border px-2 py-0.5 text-[10px] ${RUN_STATUS_STYLE[status]}`}
        >
          {RUN_STATUS_LABEL[status]}
        </span>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span
          className="h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: agent.color }}
        />
        <h2 className="font-display text-xl text-ink">{agent.name}</h2>
        {isDemo && (
          <span className="rounded-full bg-amber/10 px-2 py-0.5 text-[10px] text-amber">
            演示稿
          </span>
        )}
      </div>

      {run?.note && (
        <p className="mt-2 text-[11px] text-ink-muted">重跑备注：{run.note}</p>
      )}
      {output && Boolean(output.fallback_reason) && (
        <p className="mt-2 rounded-control bg-amber/10 px-2 py-1.5 text-[10.5px] leading-4 text-amber">
          {String(output.fallback_reason)}
        </p>
      )}
      {run?.error && (
        <p className="mt-2 rounded-control bg-apple-weak px-2 py-1.5 text-[11px] text-danger">
          {run.error}
        </p>
      )}

      <div className="mt-3 rounded-control bg-paper p-3 text-xs leading-relaxed text-ink-muted">
        {output ? (
          <OutputPreview
            agent={agent.key}
            batchId={workspace.batch.id}
            runId={run?.id ?? null}
            output={output}
            illustration={illustration}
            variants={variants}
            variant={packagingVariant}
            onVariantChange={onPackagingVariantChange}
          />
        ) : (
          "还没有产出。运行后在这里预览；审核时可编辑 JSON。"
        )}
      </div>

      {output && <Citations output={output} knowledge={knowledge} />}
      <GuardPanel run={run} />

      {run?.model && (
        <p className="mt-2 text-[10px] text-ink-muted">
          {run.model === "mock" ? "演示生成" : `模型 ${run.model}`} · {run.tokens} tokens
        </p>
      )}

      {output && (
        <details className="mt-2 text-[11px] text-ink-muted">
          <summary className="cursor-pointer">查看原始 JSON</summary>
          <pre className="mt-2 max-h-40 overflow-auto rounded-control bg-surface-2 p-2 text-[10px] leading-4">
            {JSON.stringify(output, null, 2)}
          </pre>
        </details>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {reviewable && (
          <button
            onClick={onReview}
            className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-apple-hover disabled:opacity-60"
            disabled={busy}
          >
            <ShieldCheck size={14} />
            审核产出
          </button>
        )}

        {canRun && status !== "running" && !reviewable && (
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-apple-hover disabled:opacity-60"
            disabled={busy}
          >
            {status === "failed" ? <RefreshCw size={14} /> : <Play size={14} />}
            {status === "failed" ? "重跑" : `运行${agent.short}`}
          </button>
        )}

        {reviewable && canRun && (
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 rounded-control border border-line px-3 py-2 text-xs text-ink-muted transition-colors hover:border-apple/40 hover:text-apple disabled:opacity-60"
            disabled={busy}
          >
            <RefreshCw size={14} />
            重跑
          </button>
        )}

        {status === "running" && <span className="text-xs text-apple">生成中…</span>}
        {status === "idle" && !canRun && (
          <span className="text-xs text-ink-muted">等待前序</span>
        )}
        {status === "done" && (
          <span className="text-xs text-leaf">已通过，产出已写入品牌护照</span>
        )}
      </div>
    </section>
  );
}
