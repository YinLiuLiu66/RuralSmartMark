import { ArrowLeft, Play, RefreshCw, ShieldCheck } from "lucide-react";

import type { AgentKey, BatchWorkspace } from "../api/pipeline";
import {
  agentStatus,
  latestRun,
  nextAgent,
  outputForAgent,
  RUN_STATUS_LABEL,
  RUN_STATUS_STYLE,
  type AgentMeta,
} from "../agents";

function preview(agent: AgentKey, output: Record<string, unknown> | null): string {
  if (!output) return "";

  if (agent === "story") {
    return `${String(output.ip_name ?? "故事")} · ${String(output.story_short ?? "")}`;
  }
  if (agent === "packaging") {
    return String(output.concept ?? "包装方案已生成");
  }
  if (agent === "marketing") {
    const xiaohongshu = output.xiaohongshu as { title?: string } | undefined;
    return xiaohongshu?.title ?? "内容已生成";
  }
  const premium = output.premium_pct;
  return typeof premium === "number" ? `建议溢价 ${premium}%` : "定价已生成";
}

export default function StationCard({
  agent,
  workspace,
  busy,
  onRun,
  onReview,
  onClose,
}: {
  agent: AgentMeta;
  workspace: BatchWorkspace;
  busy: boolean;
  onRun: () => void;
  onReview: () => void;
  onClose: () => void;
}) {
  const status = agentStatus(workspace, agent.key);
  const run = latestRun(workspace, agent.key);
  const output = outputForAgent(workspace, agent.key);
  const canRun =
    nextAgent(workspace.batch.state) === agent.key ||
    workspace.batch.state === `${agent.key}_review`;
  const reviewable = status === "review" && run?.status === "waiting_review";

  return (
    <section className="card p-4">
      <div className="flex items-center justify-between">
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
      </div>

      {run?.note && (
        <p className="mt-2 text-[11px] text-ink-muted">重跑备注：{run.note}</p>
      )}
      {run?.error && (
        <p className="mt-2 rounded-control bg-apple-weak px-2 py-1.5 text-[11px] text-danger">
          {run.error}
        </p>
      )}

      <div className="mt-4 rounded-control bg-paper p-3 text-xs leading-relaxed text-ink-muted">
        {output ? preview(agent.key, output) : "还没有产出。运行后在这里预览，审核时可编辑 JSON。"}
      </div>

      {output && (
        <details className="mt-3 text-[11px] text-ink-muted">
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
            className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            disabled={busy}
          >
            <ShieldCheck size={14} />
            审核产出
          </button>
        )}

        {canRun && status !== "running" && !reviewable && (
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            disabled={busy}
          >
            {status === "failed" ? <RefreshCw size={14} /> : <Play size={14} />}
            {status === "failed" ? "重跑" : `运行${agent.short}`}
          </button>
        )}

        {reviewable && canRun && (
          <button
            onClick={onRun}
            className="flex items-center gap-1.5 rounded-control border border-line px-3 py-2 text-xs text-ink-muted disabled:opacity-60"
            disabled={busy}
          >
            <RefreshCw size={14} />
            重跑
          </button>
        )}

        {status === "running" && (
          <span className="text-xs text-apple">生成中…</span>
        )}
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
