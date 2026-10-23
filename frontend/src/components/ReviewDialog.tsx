import { useEffect, useRef, useState } from "react";
import { ExternalLink, TriangleAlert } from "lucide-react";

import type { KnowledgeDoc } from "../api/client";
import type { GuardResult } from "../api/pipeline";
import type { AgentMeta } from "../agents";

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

function ReviewEvidence({
  output,
  knowledge,
  guard,
}: {
  output: Record<string, unknown> | null;
  knowledge: Record<string, KnowledgeDoc>;
  guard: GuardResult | null;
}) {
  const citations = citationsOf(output);
  const issues = [...(guard?.warnings ?? []), ...(guard?.errors ?? [])];
  return (
    <div className="mb-3 space-y-2">
      {citations.length > 0 && (
        <div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-ink-muted">
            引用证据 · {citations.length}
          </div>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {citations.map((citation, index) => {
              const doc = knowledge[citation.doc_id];
              const demo = doc?.credibility === "demo" || citation.doc_id.startsWith("DEMO");
              const url = doc?.source_url?.startsWith("http") ? doc.source_url : null;
              return url ? (
                <a
                  key={`${citation.doc_id}-${index}`}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  title={citation.quote}
                  className="inline-flex max-w-full items-center gap-1 rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] text-ink-muted hover:border-apple/40 hover:text-apple"
                >
                  <span className="truncate">
                    {citation.doc_id}
                    {doc ? ` · ${doc.title}` : ""}
                  </span>
                  <ExternalLink size={10} className="shrink-0" />
                  {demo && <span className="shrink-0 text-amber">演示</span>}
                </a>
              ) : (
                <span
                  key={`${citation.doc_id}-${index}`}
                  title={citation.quote}
                  className="inline-flex max-w-full items-center gap-1 rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] text-ink-muted"
                >
                  <span className="truncate">
                    {citation.doc_id}
                    {doc ? ` · ${doc.title}` : ""}
                  </span>
                  {demo && <span className="shrink-0 text-amber">演示</span>}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {issues.length > 0 && (
        <div className="space-y-1">
          {issues.slice(0, 5).map((issue) => (
            <div
              key={`${issue.rule}-${issue.field}-${issue.message}`}
              className={`flex gap-1.5 rounded-control px-2 py-1.5 text-[10.5px] leading-4 ${
                issue.severity === "error"
                  ? "bg-apple-weak text-danger"
                  : "bg-amber/10 text-amber"
              }`}
            >
              <TriangleAlert size={12} className="mt-0.5 shrink-0" />
              <span>
                <b className="font-medium">{issue.rule}</b> · {issue.message}
              </span>
            </div>
          ))}
          {issues.length > 5 && (
            <p className="text-[10px] text-ink-muted">还有 {issues.length - 5} 条预警。</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function ReviewDialog({
  open,
  agent,
  batchId,
  output,
  guard,
  knowledge,
  busy,
  onClose,
  onApprove,
  onReject,
}: {
  open: boolean;
  agent: AgentMeta;
  batchId: number | null;
  output: Record<string, unknown> | null;
  guard: GuardResult | null;
  knowledge: Record<string, KnowledgeDoc>;
  busy: boolean;
  onClose: () => void;
  onApprove: (output: Record<string, unknown>) => Promise<void>;
  onReject: (note: string) => Promise<void>;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [text, setText] = useState("{}");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      setText(JSON.stringify(output ?? {}, null, 2));
      setNote("");
      setError(null);
    }
    if (!open && dialog.open) dialog.close();
  }, [open, output]);

  async function handleApprove() {
    setError(null);
    try {
      const parsed = JSON.parse(text) as unknown;
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("产出必须是 JSON 对象");
      }
      await onApprove(parsed as Record<string, unknown>);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "审核失败");
    }
  }

  async function handleReject() {
    setError(null);
    try {
      await onReject(note);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "驳回失败");
    }
  }

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onCancel={(event) => {
        if (busy) event.preventDefault();
      }}
      aria-labelledby="review-title"
      className="w-[min(860px,calc(100vw-32px))] rounded-card border border-line bg-surface p-0 text-ink shadow-card"
    >
      <div className="flex max-h-[90vh] flex-col">
        <header className="flex items-start justify-between border-b border-line px-5 py-4">
          <div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-ink-muted">
              人工审核 · 通过前服务端会再跑一次 FactGuard
            </div>
            <h2 id="review-title" className="mt-1 font-display text-2xl">
              {agent.name}
            </h2>
          </div>
          <button
            onClick={() => dialogRef.current?.close()}
            className="rounded-control border border-line px-2 py-1 text-[11px] text-ink-muted transition-colors hover:border-apple/40 hover:text-apple disabled:opacity-50"
            disabled={busy}
          >
            关闭
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <ReviewEvidence output={output} knowledge={knowledge} guard={guard} />

          {agent.key === "packaging" && batchId && (
            <div className="mb-3 overflow-hidden rounded-control border border-line bg-surface-2">
              <img
                src={`/api/batches/${batchId}/agents/packaging/preview`}
                alt="包装示意预览"
                className="aspect-[8/5] w-full object-contain"
              />
            </div>
          )}

          <p className="mb-3 text-[11px] leading-relaxed text-ink-muted">
            直接修改下面的 JSON 再通过。数字字段（价格、成本、溢价率）在服务端按定价计算器重算；
            引用必须逐字来自知识库，否则会被 422 拦截。
          </p>

          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            spellCheck={false}
            className="h-[340px] w-full resize-y rounded-control border border-line bg-paper p-3 font-mono text-[11px] leading-5 text-ink outline-none focus:border-apple"
          />

          {error && (
            <p className="mt-2 rounded-control bg-apple-weak px-3 py-2 text-xs text-danger">
              {error}
            </p>
          )}

          <label className="mt-3 block text-[11px] text-ink-muted">
            驳回备注（可选）
            <input
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="例如：再乡土一点 / 少用形容词"
              className="mt-1 w-full rounded-control border border-line bg-paper px-3 py-2 text-xs text-ink outline-none focus:border-apple"
            />
          </label>
        </div>

        <footer className="flex items-center justify-end gap-2 border-t border-line px-5 py-3">
          <button
            onClick={() => void handleReject()}
            className="rounded-control border border-danger/30 px-3 py-2 text-xs text-danger transition-colors hover:border-danger/50 hover:bg-danger/5 disabled:opacity-60"
            disabled={busy}
          >
            驳回
          </button>
          <button
            onClick={() => void handleApprove()}
            className="rounded-control bg-apple px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-apple-hover disabled:opacity-60"
            disabled={busy}
          >
            {busy ? "处理中…" : "通过并进入下一站"}
          </button>
        </footer>
      </div>
    </dialog>
  );
}
