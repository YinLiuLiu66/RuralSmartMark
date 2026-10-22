import { useEffect, useRef, useState } from "react";
import { ArrowUpRight, Loader2, Send, ShieldCheck, Sparkles, X } from "lucide-react";

import { controllerApi, type ControllerSession } from "../api/controller";

const ACTION_LABEL: Record<string, string> = {
  commit_product: "确认建档",
  approve_agent: "确认通过",
  reject_agent: "确认驳回",
  rewind_to_agent: "确认回退并重跑",
};

export default function ControllerPanel({
  productSlug,
  batchId,
  onClose,
  onDataChanged,
  inline = false,
}: {
  productSlug: string | null;
  batchId: number | null;
  onClose: () => void;
  onDataChanged: () => void;
  inline?: boolean;
}) {
  const [session, setSession] = useState<ControllerSession | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setSession(null);
    setError(null);
    controllerApi
      .createSession(productSlug, batchId)
      .then((result) => {
        if (!cancelled) setSession(result);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "总控初始化失败");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [productSlug, batchId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [session?.messages.length, busy]);

  async function send(text: string) {
    if (!session || busy || !text.trim()) return;
    const message = text.trim().slice(0, 2000);
    setInput("");
    setBusy(true);
    setError(null);
    try {
      const turn = await controllerApi.sendMessage(session.id, message);
      setSession(turn.session);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "总控没有回应");
    } finally {
      setBusy(false);
    }
  }

  async function confirm(decision: "confirm" | "cancel") {
    if (!session?.pending_action_json || busy) return;
    setBusy(true);
    setError(null);
    try {
      const turn = await controllerApi.confirm(
        session.id,
        session.pending_action_json.id,
        decision,
      );
      setSession(turn.session);
      if (decision === "confirm") onDataChanged();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "确认失败");
    } finally {
      setBusy(false);
    }
  }

  const draft = session?.draft_json;
  const pending = session?.pending_action_json;
  const questions = draft?.questions ?? [];

  return (
    <aside
      className={
        inline
          ? "relative mx-auto flex h-dvh w-full max-w-[720px] flex-col border-x border-line bg-paper"
          : "fixed right-0 top-0 z-40 flex h-dvh w-full max-w-[430px] flex-col border-l border-line bg-paper shadow-[-20px_0_60px_rgba(31,42,36,0.16)]"
      }
    >
      <header className="flex items-center justify-between border-b border-line bg-surface px-4 py-3">
        <div>
          <div className="flex items-center gap-2 font-display text-lg text-ink">
            <Sparkles size={16} className="text-apple" />
            总控
          </div>
          <p className="mt-0.5 text-[10px] text-ink-faint">
            调研 · 运行 · 修改 · 审核，都在这里说
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="关闭总控"
          className="flex h-8 w-8 items-center justify-center rounded-control border border-line text-ink-muted"
        >
          <X size={15} />
        </button>
      </header>

      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {!session && !error && (
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <Loader2 size={14} className="animate-spin" />
            正在连接总控…
          </div>
        )}

        {session?.messages.length === 0 && !busy && (
          <div className="rounded-card border border-dashed border-line bg-surface p-4">
            <p className="text-sm leading-6 text-ink">
              告诉我你想做什么产品，或者直接问当前批次。
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {["帮我做一个新产品", "现在到哪了", "包装改克制一点"].map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => void send(item)}
                  className="rounded-full border border-line bg-paper px-3 py-1.5 text-[11px] text-ink-muted"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {session?.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[88%] whitespace-pre-line break-words rounded-card px-3.5 py-2.5 text-[13px] leading-6 ${
                message.role === "user"
                  ? "rounded-br-md bg-apple text-white"
                  : "rounded-bl-md border border-line bg-surface text-ink-muted"
              }`}
            >
              {message.role === "assistant" && (
                <div className="mb-1 flex items-center gap-1 text-[10px] text-ink-faint">
                  <ShieldCheck size={11} />
                  总控
                </div>
              )}
              {message.content}
            </div>
          </div>
        ))}

        {draft && (
          <section className="rounded-card border border-line bg-surface p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[10px] uppercase tracking-[0.18em] text-ink-faint">
                产品档案草案
              </span>
              <span className="rounded-full bg-apple-weak px-2 py-0.5 text-[10px] text-apple">
                {draft.docs?.length ?? 0} 条知识库
              </span>
            </div>
            <div className="mt-2 font-display text-xl text-ink">
              {draft.product?.name ?? "未命名产品"}
            </div>
            <div className="mt-1 text-[11px] text-ink-muted">
              {draft.product?.county ?? "产地待补"} · {draft.product?.form ?? "规格待补"}
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-ink-muted">
              <span>基准价：{draft.benchmarks?.length ?? 0} 档</span>
              <span>来源：{draft.docs?.length ?? 0} 条</span>
            </div>
            {questions.length > 0 && (
              <div className="mt-3 rounded-control bg-amber/10 px-3 py-2 text-[11px] leading-5 text-amber">
                <div className="font-medium">还需要你确认</div>
                <ul className="mt-1 list-disc pl-4">
                  {questions.slice(0, 5).map((question) => (
                    <li key={question}>{question}</li>
                  ))}
                </ul>
              </div>
            )}
            {(draft.warnings?.length ?? 0) > 0 && (
              <div className="mt-2 space-y-1 text-[10px] leading-4 text-ink-faint">
                {draft.warnings?.slice(0, 3).map((warning) => (
                  <p key={warning}>提示：{warning}</p>
                ))}
              </div>
            )}
          </section>
        )}

        {pending && (
          <section className="rounded-card border border-apple/30 bg-apple-weak/60 p-4">
            <div className="text-[10px] uppercase tracking-[0.18em] text-apple">
              需要确认
            </div>
            <div className="mt-1.5 text-sm font-medium text-ink">
              {ACTION_LABEL[pending.kind] ?? pending.kind}
            </div>
            <p className="mt-1 text-xs leading-5 text-ink-muted">{pending.summary}</p>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void confirm("confirm")}
                className="flex-1 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
              >
                确认
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void confirm("cancel")}
                className="rounded-control border border-line bg-surface px-3 py-2 text-xs text-ink-muted disabled:opacity-50"
              >
                取消
              </button>
            </div>
          </section>
        )}

        {busy && (
          <div className="flex items-center gap-2 text-xs text-ink-faint">
            <Loader2 size={14} className="animate-spin" />
            总控正在看资料 / 调用 Agent…
          </div>
        )}

        {error && (
          <div role="alert" className="rounded-control border border-danger/30 bg-surface px-3 py-2 text-[11px] leading-5 text-danger">
            {error}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="flex items-center gap-2 border-t border-line bg-surface px-4 py-3"
        onSubmit={(event) => {
          event.preventDefault();
          void send(input);
        }}
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          maxLength={2000}
          placeholder="例如：帮我做贵州麻江蓝莓 / 包装改克制 / 通过故事"
          className="min-w-0 flex-1 rounded-full border border-line bg-paper px-4 py-2.5 text-[16px] text-ink outline-none placeholder:text-ink-faint focus:border-apple/50"
        />
        <button
          type="submit"
          disabled={busy || !input.trim() || !session}
          aria-label="发送给总控"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-apple text-white disabled:opacity-40"
        >
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </form>
      <div className="border-t border-line px-4 py-2 text-[10px] text-ink-faint">
        建档、通过、驳回、回退会先弹确认；调研来源会逐字校验。
        <ArrowUpRight size={10} className="ml-1 inline" />
      </div>
    </aside>
  );
}
