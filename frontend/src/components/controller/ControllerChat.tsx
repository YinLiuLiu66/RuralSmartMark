import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowUpRight,
  Brain,
  ChevronRight,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import type { ControllerMessage } from "../../api/controller";
import { STATUS_LABEL } from "../../agents";
import { useControllerStore } from "../../stores/controller";
import { toApiContext, type PageContext } from "../../hooks/usePageContext";

const ACTION_LABEL: Record<string, string> = {
  commit_product: "确认建档",
  create_batch: "确认新建批次",
  approve_agent: "确认通过并继续下一站",
  reject_agent: "确认驳回",
  rewind_to_agent: "确认回退并重跑",
  delete_batch: "确认删除批次",
  apply_inputs: "确认写入档案",
};

const TOOL_LABEL: Record<string, string> = {
  list_products: "正在读取产品列表",
  list_batches: "正在读取批次列表",
  get_workspace: "正在读取批次状态",
  research_product: "正在检索资料并整理档案",
  record_inputs: "正在整理你提供的数据",
  run_agent: "正在调用 Agent",
  request_action: "正在准备确认卡",
};

function latestToolLabel(tools: string[]): string {
  const latest = tools[tools.length - 1];
  if (!latest) return "总控正在思考…";
  return TOOL_LABEL[latest] ?? `正在执行 ${latest}`;
}

function thinkingLines(text: string): string[] {
  if (!text.trim()) return [];
  const lines: string[] = [];
  for (const paragraph of text.split(/\n+/)) {
    let rest = paragraph.trim();
    if (!rest) continue;
    while (rest.length > 110) {
      const window = rest.slice(0, 110);
      const cut = Math.max(
        window.lastIndexOf("。"),
        window.lastIndexOf("；"),
        window.lastIndexOf("！"),
        window.lastIndexOf("？"),
        window.lastIndexOf("."),
        window.lastIndexOf(";"),
      );
      const index = cut >= 20 ? cut + 1 : 110;
      lines.push(rest.slice(0, index).trim());
      rest = rest.slice(index).trim();
    }
    if (rest) lines.push(rest);
  }
  return lines;
}

function messageThinking(message: ControllerMessage): string[] {
  const raw = message.action_json?.thinking;
  if (!Array.isArray(raw)) return [];
  return raw.filter(
    (line): line is string => typeof line === "string" && line.trim().length > 0,
  );
}

function ThinkingBlock({
  lines,
  streaming = false,
}: {
  lines: string[];
  streaming?: boolean;
}) {
  if (!streaming && lines.length === 0) return null;
  return (
    <details className="group mb-2 rounded-control border border-line/70 bg-paper/70 px-2.5 py-2">
      <summary className="flex cursor-pointer list-none select-none items-center gap-1.5 text-[10px] text-ink-faint [&::-webkit-details-marker]:hidden">
        <ChevronRight size={11} className="transition-transform group-open:rotate-90" />
        {streaming ? (
          <Loader2 size={11} className="animate-spin" />
        ) : (
          <Brain size={11} />
        )}
        {streaming ? "思考中" : "思考过程"}
      </summary>
      <div className="mt-2 space-y-1.5 border-t border-line/60 pt-2">
        {lines.map((line, index) => (
          <p
            key={`${index}-${line.slice(0, 12)}`}
            className="whitespace-pre-wrap break-words text-[11px] leading-5 text-ink-faint"
          >
            {line}
          </p>
        ))}
      </div>
    </details>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[88%] whitespace-pre-line break-words rounded-card rounded-br-md bg-apple px-3.5 py-2.5 text-[13px] leading-6 text-white">
        {text}
      </div>
    </div>
  );
}

function AssistantBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[88%] whitespace-pre-line break-words rounded-card rounded-bl-md border border-line bg-surface px-3.5 py-2.5 text-[13px] leading-6 text-ink-muted">
        <div className="mb-1 flex items-center gap-1 text-[10px] text-ink-faint">
          <ShieldCheck size={11} />
          总控
        </div>
        {children}
      </div>
    </div>
  );
}

function contextLabel(context: PageContext): string {
  if (context.productName) {
    const parts = [context.productName];
    parts.push(context.batchCode ?? "未选批次");
    if (context.batchState) {
      parts.push(STATUS_LABEL[context.batchState] ?? context.batchState);
    }
    return parts.join(" · ");
  }
  if (context.route === "workbench") return "工作台 · 未选择项目";
  return "全页聊天 · 未选择项目";
}

export default function ControllerChat({
  context,
  variant = "dock",
  onClose,
}: {
  context: PageContext;
  variant?: "dock" | "page";
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const session = useControllerStore((state) => state.session);
  const busy = useControllerStore((state) => state.busy);
  const error = useControllerStore((state) => state.error);
  const pendingUser = useControllerStore((state) => state.pendingUser);
  const stream = useControllerStore((state) => state.stream);
  const needsTarget = useControllerStore((state) => state.needsTarget);
  const ensureSession = useControllerStore((state) => state.ensureSession);
  const refresh = useControllerStore((state) => state.refresh);
  const send = useControllerStore((state) => state.send);
  const confirm = useControllerStore((state) => state.confirm);

  useEffect(() => {
    void ensureSession();
  }, [ensureSession]);

  useEffect(() => {
    const reload = () => void refresh();
    window.addEventListener("focus", reload);
    return () => window.removeEventListener("focus", reload);
  }, [refresh]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [session?.messages.length, pendingUser, stream?.answer, stream?.thinking, busy]);

  function submit() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    void send(text, toApiContext(context));
  }

  async function handleConfirm(decision: "confirm" | "cancel") {
    const kind = session?.pending_action_json?.kind;
    const turn = await confirm(decision);
    if (!turn || decision !== "confirm") return;
    const next = turn.session;
    if (kind === "commit_product") {
      // 新产品建档后回工作台，卡片由 dataVersion 触发刷新生成。
      navigate("/");
      return;
    }
    if (kind === "create_batch") {
      if (context.product_slug && next.batch_id) {
        navigate(`/project/${context.product_slug}?batch=${next.batch_id}`);
      }
      return;
    }
    if (kind === "delete_batch" && context.product_slug) {
      navigate(`/project/${context.product_slug}`);
    }
  }

  const draft = session?.draft_json;
  const pending = session?.pending_action_json;
  const questions = draft?.questions ?? [];
  const streamLines = stream ? thinkingLines(stream.thinking) : [];

  return (
    <aside
      className={
        variant === "page"
          ? "relative mx-auto flex h-dvh w-full max-w-[720px] flex-col border-x border-line bg-paper"
          : "fixed right-0 top-0 z-40 flex h-dvh w-full max-w-[430px] flex-col border-l border-line bg-paper shadow-[-20px_0_60px_rgba(31,42,36,0.16)]"
      }
    >
      <header className="flex items-center justify-between border-b border-line bg-surface px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 font-display text-lg text-ink">
            <Sparkles size={16} className="text-apple" />
            总控
          </div>
          <p
            className="mt-0.5 max-w-[250px] truncate text-[10px] text-ink-muted"
            title={contextLabel(context)}
          >
            {contextLabel(context)}
          </p>
          {session?.product_name && (
            <p className="mt-0.5 max-w-[250px] truncate text-[10px] text-ink-faint">
              最近操作：{session.product_name} · {session.batch_code ?? "未绑定批次"}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="关闭总控"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-control border border-line text-ink-muted transition-colors hover:border-apple/40 hover:text-apple"
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

        {session?.messages.length === 0 && !busy && !pendingUser && (
          <div className="rounded-card border border-dashed border-line bg-surface p-4">
            <p className="text-sm leading-6 text-ink">
              告诉我你想做什么产品，或者直接问当前项目。
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {["帮我做一个新产品", "我现在有哪些项目", "现在到哪了"].map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => void send(item, toApiContext(context))}
                  className="rounded-full border border-line bg-paper px-3 py-1.5 text-[11px] text-ink-muted transition-colors hover:border-apple/30 hover:bg-apple-weak/40 hover:text-apple"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {session?.messages.map((message) => {
          if (message.role === "user") {
            return <UserBubble key={message.id} text={message.content} />;
          }
          const tracedLines = messageThinking(message);
          return (
            <AssistantBubble key={message.id}>
              {tracedLines.length > 0 && <ThinkingBlock lines={tracedLines} />}
              {message.content}
            </AssistantBubble>
          );
        })}

        {pendingUser && <UserBubble text={pendingUser} />}

        {stream && (
          <AssistantBubble>
            {stream.thinking.trim() && (
              <ThinkingBlock lines={streamLines} streaming={stream.active} />
            )}
            {stream.answer ? (
              <div>
                {stream.answer}
                <span className="ml-0.5 inline-block h-3.5 w-1 animate-pulse bg-apple/70 align-middle" />
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-[11px] text-ink-faint">
                <Loader2 size={12} className="animate-spin" />
                {latestToolLabel(stream.tools)}
              </div>
            )}
          </AssistantBubble>
        )}

        {needsTarget && needsTarget.candidates.length > 0 && (
          <section className="rounded-card border border-amber/40 bg-amber/5 p-3">
            <div className="text-[10px] uppercase tracking-[0.18em] text-amber">
              需要指定目标
            </div>
            <p className="mt-1 text-[11px] leading-5 text-ink-muted">
              {needsTarget.message}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {needsTarget.candidates.map((candidate) => (
                <button
                  key={`${candidate.kind}-${candidate.batch_id ?? candidate.product_slug}`}
                  type="button"
                  onClick={() => {
                    const target =
                      candidate.kind === "batch" && candidate.batch_id
                        ? `/project/${candidate.product_slug}?batch=${candidate.batch_id}`
                        : `/project/${candidate.product_slug}`;
                    navigate(target);
                  }}
                  className="rounded-full border border-line bg-surface px-2.5 py-1 text-[11px] text-ink-muted hover:border-apple/40 hover:text-apple"
                >
                  {candidate.label}
                </button>
              ))}
            </div>
          </section>
        )}

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
            {pending.batch_code && (
              <p className="mt-1 text-[10px] text-ink-faint">
                目标批次：{pending.batch_code}（出卡时已固定）
              </p>
            )}
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleConfirm("confirm")}
                className="flex-1 rounded-control bg-apple px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-apple-hover disabled:opacity-50"
              >
                确认
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => void handleConfirm("cancel")}
                className="rounded-control border border-line bg-surface px-3 py-2 text-xs text-ink-muted transition-colors hover:border-line-strong hover:text-ink disabled:opacity-50"
              >
                取消
              </button>
            </div>
          </section>
        )}

        {busy && !stream && (
          <div className="flex items-center gap-2 text-xs text-ink-faint">
            <Loader2 size={14} className="animate-spin" />
            总控正在处理…
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="rounded-control border border-danger/30 bg-surface px-3 py-2 text-[11px] leading-5 text-danger"
          >
            {error}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="flex items-center gap-2 border-t border-line bg-surface px-4 py-3"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
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
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-apple text-white transition-colors hover:bg-apple-hover disabled:opacity-40"
        >
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
        </button>
      </form>
      <div className="border-t border-line px-4 py-2 text-[10px] text-ink-faint">
        建档、通过、驳回、回退会先弹确认；目标批次在出卡时固定。
        <ArrowUpRight size={10} className="ml-1 inline" />
      </div>
    </aside>
  );
}
