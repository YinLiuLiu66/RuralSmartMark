import { useEffect, useRef, useState } from "react";

import type { AgentMeta } from "../agents";

export default function ReviewDialog({
  open,
  agent,
  output,
  busy,
  onClose,
  onApprove,
  onReject,
}: {
  open: boolean;
  agent: AgentMeta;
  output: Record<string, unknown> | null;
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
      className="w-[min(760px,calc(100vw-32px))] rounded-card border border-line bg-surface p-0 text-ink shadow-card"
    >
      <div className="flex max-h-[85vh] flex-col">
        <header className="flex items-start justify-between border-b border-line px-5 py-4">
          <div>
            <div className="text-[10px] uppercase tracking-[0.18em] text-ink-muted">
              人工审核
            </div>
            <h2 id="review-title" className="mt-1 font-display text-2xl">
              {agent.name}
            </h2>
          </div>
          <button
            onClick={() => dialogRef.current?.close()}
            className="rounded-control border border-line px-2 py-1 text-[11px] text-ink-muted"
            disabled={busy}
          >
            关闭
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <p className="mb-3 text-[11px] leading-relaxed text-ink-muted">
            Phase 1 先用 JSON 审核；Phase 2 会换成故事、包装、内容、定价各自的表单。
            直接改下面的 JSON，再点“通过并进入下一站”。
          </p>

          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            spellCheck={false}
            className="h-[360px] w-full resize-y rounded-control border border-line bg-paper p-3 font-mono text-[11px] leading-5 text-ink outline-none focus:border-apple"
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
            className="rounded-control border border-danger/30 px-3 py-2 text-xs text-danger disabled:opacity-60"
            disabled={busy}
          >
            驳回
          </button>
          <button
            onClick={() => void handleApprove()}
            className="rounded-control bg-apple px-4 py-2 text-xs font-medium text-white disabled:opacity-60"
            disabled={busy}
          >
            {busy ? "处理中…" : "通过并进入下一站"}
          </button>
        </footer>
      </div>
    </dialog>
  );
}
