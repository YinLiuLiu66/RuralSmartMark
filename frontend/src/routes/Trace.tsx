import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  BadgePercent,
  ChevronDown,
  ExternalLink,
  Leaf,
  MapPin,
  MessageCircle,
  QrCode,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import {
  traceApi,
  TraceNotFoundError,
  type Trace,
  type TraceEvidence,
  type TraceTimelineEvent,
} from "../api/trace";

type PageState = "loading" | "ready" | "not-found" | "error";
type ChatEntry = { role: "user" | "assistant"; content: string; source?: "llm" | "template" };

function formatPct(value: number): string {
  return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
}

function formatDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function SectionHeading({
  eyebrow,
  title,
  note,
}: {
  eyebrow: string;
  title: string;
  note?: string;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.22em] text-apple">{eyebrow}</div>
      <h2 className="mt-1.5 font-display text-[26px] leading-tight text-ink">{title}</h2>
      {note && <p className="mt-2 text-xs leading-6 text-ink-muted">{note}</p>}
    </div>
  );
}

function CopyRow({ label, text, emphasis = false }: { label: string; text: string; emphasis?: boolean }) {
  return (
    <div className="border-b border-line/70 pb-3 last:border-0 last:pb-0">
      <div className="text-[10px] uppercase tracking-[0.18em] text-ink-faint">{label}</div>
      <p className={`mt-1.5 text-sm leading-7 ${emphasis ? "font-display text-lg leading-8 text-ink" : "text-ink-muted"}`}>
        {text}
      </p>
    </div>
  );
}

function EvidenceList({ items }: { items: TraceEvidence[] }) {
  if (items.length === 0) return null;
  return (
    <details className="group mt-5 rounded-card border border-line bg-surface">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-xs text-ink">
        <span className="flex items-center gap-2">
          <ShieldCheck size={14} className="text-leaf" />
          事实与来源
        </span>
        <span className="flex items-center gap-2 text-[11px] text-ink-faint">
          {items.length} 条
          <ChevronDown size={14} className="transition group-open:rotate-180" />
        </span>
      </summary>
      <ul className="space-y-4 border-t border-line px-4 py-4">
        {items.map((item) => {
          const external = item.source_url?.startsWith("http");
          return (
            <li key={`${item.doc_id}-${item.quote.slice(0, 12)}`} className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-ink-muted">
                  {item.doc_id}
                </span>
                {item.credibility === "demo" && (
                  <span className="rounded-full bg-apple-weak px-2 py-0.5 text-[10px] text-apple">
                    演示设定
                  </span>
                )}
                <span className="min-w-0 truncate text-[11px] text-ink-faint">{item.title}</span>
              </div>
              <p className="mt-1.5 break-words text-xs leading-6 text-ink-muted">“{item.quote}”</p>
              {external ? (
                <a
                  href={item.source_url ?? undefined}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-[11px] text-leaf underline underline-offset-4"
                >
                  {item.source_date ?? "来源"}
                  <ExternalLink size={11} />
                </a>
              ) : (
                <div className="mt-1 text-[11px] text-ink-faint">
                  {item.source_date ?? "演示条目"} · 非外部事实
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

function Timeline({ events, withTime = false }: { events: TraceTimelineEvent[]; withTime?: boolean }) {
  return (
    <ol className="mt-5 border-l border-line">
      {events.map((event, index) => (
        <li key={`${event.step}-${index}`} className="relative pb-5 pl-6 last:pb-0">
          <span className="absolute -left-[9px] top-0 flex h-[18px] w-[18px] items-center justify-center rounded-full border border-line bg-paper text-[9px] text-ink-muted">
            {index + 1}
          </span>
          <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
            <span className="text-sm font-medium text-ink">{event.step}</span>
            {withTime && formatDate(event.at) && (
              <span className="text-[10px] tabular-nums text-ink-faint">{formatDate(event.at)}</span>
            )}
          </div>
          <p className="mt-1 break-words text-xs leading-6 text-ink-muted">{event.note}</p>
        </li>
      ))}
    </ol>
  );
}

function Skeleton() {
  return (
    <div className="min-h-dvh bg-paper" aria-busy="true" aria-label="溯源页加载中">
      <div className="mx-auto max-w-[430px] animate-pulse">
        <div className="bg-ink px-6 pb-10 pt-6">
          <div className="h-3 w-24 rounded bg-paper/15" />
          <div className="mt-10 h-9 w-48 rounded bg-paper/15" />
          <div className="mt-3 h-9 w-36 rounded bg-paper/15" />
          <div className="mt-5 h-12 w-full rounded bg-paper/10" />
        </div>
        <div className="-mt-6 px-5">
          <div className="aspect-[8/5] rounded-card border border-line bg-surface-2" />
        </div>
        <div className="mt-8 space-y-3 px-5">
          <div className="h-3 w-20 rounded bg-line" />
          <div className="h-5 w-52 rounded bg-line" />
          <div className="h-3 w-full rounded bg-line/70" />
          <div className="h-3 w-11/12 rounded bg-line/70" />
          <div className="h-3 w-4/5 rounded bg-line/70" />
        </div>
      </div>
    </div>
  );
}

function ErrorPanel({
  state,
  code,
  onRetry,
}: {
  state: "not-found" | "error";
  code: string;
  onRetry: () => void;
}) {
  const notFound = state === "not-found";
  return (
    <div className="flex min-h-dvh items-center justify-center bg-paper px-6">
      <div className="w-full max-w-[360px] text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-surface-2 text-ink-muted">
          {notFound ? <QrCode size={24} /> : <RefreshCw size={22} />}
        </div>
        <h1 className="mt-5 font-display text-2xl text-ink">
          {notFound ? "这个码没有记录" : "溯源页加载失败"}
        </h1>
        <p className="mt-3 break-words text-sm leading-7 text-ink-muted">
          {notFound
            ? `溯源码「${code || "未提供"}」不在演示库里。请确认二维码完整，或打开固定演示码。`
            : "可能是网络或服务暂时不可用。页面内容不会丢，重试即可。"}
        </p>
        <div className="mt-6 flex flex-col gap-2">
          {notFound ? (
            <>
              <Link
                to="/trace/ZTDEMO26"
                className="rounded-control bg-apple px-4 py-3 text-sm font-medium text-white"
              >
                打开固定演示码 ZTDEMO26
              </Link>
              <Link
                to="/"
                className="rounded-control border border-line px-4 py-3 text-sm text-ink-muted"
              >
                返回桌面沙盘
              </Link>
            </>
          ) : (
            <button
              type="button"
              onClick={onRetry}
              className="rounded-control bg-apple px-4 py-3 text-sm font-medium text-white"
            >
              重新加载
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Trace() {
  const { code = "" } = useParams();
  const [pageState, setPageState] = useState<PageState>("loading");
  const [trace, setTrace] = useState<Trace | null>(null);
  const [scanCount, setScanCount] = useState(0);
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  function load() {
    setPageState("loading");
    traceApi
      .get(code)
      .then((result) => {
        setTrace(result);
        setScanCount(result.scan_count);
        setMessages([
          {
            role: "assistant",
            content:
              result.pricing.persona_greeting ||
              `我是${result.story.ip_name}。这一页只记录这一批有据可查的事。`,
            source: "template",
          },
        ]);
        setPageState("ready");
      })
      .catch((error: unknown) => {
        setPageState(error instanceof TraceNotFoundError ? "not-found" : "error");
      });
  }

  useEffect(() => {
    setTrace(null);
    setMessages([]);
    setInput("");
    setChatError(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  useEffect(() => {
    if (!trace) return;
    const key = `trace-scan:${trace.trace_code}`;
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, "1");
    traceApi
      .scan(trace.trace_code)
      .then((result) => setScanCount(result.scan_count))
      .catch(() => sessionStorage.removeItem(key));
  }, [trace]);

  useEffect(() => {
    if (messages.length <= 1 && !busy) return;
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, busy]);

  async function sendMessage(text: string, appendUser = true) {
    if (!trace || busy || !text.trim()) return;
    const content = text.trim().slice(0, 300);
    if (appendUser) {
      setMessages((previous) => [...previous, { role: "user", content }]);
    }
    setInput("");
    setChatError(null);
    setBusy(true);
    try {
      const result = await traceApi.chat(trace.trace_code, content);
      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: result.reply, source: result.source },
      ]);
    } catch {
      setChatError("守园人暂时没回应，请再试一次。");
    } finally {
      setBusy(false);
    }
  }

  function retryChat() {
    const lastUser = [...messages].reverse().find((item) => item.role === "user");
    if (lastUser) void sendMessage(lastUser.content, false);
  }

  if (pageState === "loading") return <Skeleton />;
  if (pageState !== "ready" || !trace) {
    return (
      <ErrorPanel
        state={pageState === "not-found" ? "not-found" : "error"}
        code={code}
        onRetry={load}
      />
    );
  }

  const gift = trace.pricing.price_ladder.find((item) => item.channel === "品牌礼盒") ??
    trace.pricing.price_ladder[trace.pricing.price_ladder.length - 1];
  const suggestions = trace.pricing.faq.slice(0, 3).map((item) => item.q);
  const costMax = Math.max(...Object.values(trace.pricing.cost_breakdown), 1);
  const lastUserMessage = [...messages].reverse().find((item) => item.role === "user");

  return (
    <div className="min-h-dvh bg-paper pb-12">
      <div className="mx-auto min-h-dvh max-w-[430px] bg-paper shadow-[0_0_60px_rgba(31,42,36,0.08)]">
        <header
          className="relative overflow-hidden bg-ink px-6 pb-9 pt-5 text-paper"
          style={{
            backgroundImage:
              "radial-gradient(circle at 88% 0%, rgba(201,164,106,0.22), transparent 52%)",
          }}
        >
          <div className="flex items-center justify-between gap-3">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-[11px] text-paper/65 underline-offset-4 hover:underline"
            >
              <ArrowLeft size={14} />
              乡土印记
            </Link>
            <span className="rounded-full border border-paper/20 px-2.5 py-1 text-[10px] tracking-wide text-paper/70">
              {trace.fixed_demo ? "固定演示批次" : "演示溯源"}
            </span>
          </div>

          <div className="mt-9 flex items-center gap-2 text-[10px] uppercase tracking-[0.24em] text-paper/50">
            <QrCode size={14} />
            TRACE / {trace.trace_code}
          </div>
          <h1 className="mt-3 font-display text-[34px] leading-[1.22]">
            这箱苹果，
            <br />
            从乌蒙山来。
          </h1>
          <p className="mt-4 text-sm leading-7 text-paper/75">
            {trace.pricing.persona_greeting || trace.story.story_short}
          </p>

          <div className="mt-6 flex flex-wrap gap-x-4 gap-y-2 text-[11px] text-paper/60">
            <span className="inline-flex items-center gap-1">
              <Leaf size={12} />
              {trace.product.brand_name}
            </span>
            <span className="inline-flex items-center gap-1">
              <MapPin size={12} />
              {trace.product.county}
            </span>
            <span className="tabular-nums">批次 {trace.batch.code}</span>
            <span className="tabular-nums">{trace.batch.quantity_kg} kg</span>
          </div>
        </header>

        <div className="-mt-5 px-5">
          <figure className="overflow-hidden rounded-card border border-line bg-surface shadow-card">
            <img
              src={trace.packaging.image_url}
              alt={`${trace.product.brand_name}包装示意`}
              className="aspect-[8/5] w-full object-cover"
              loading="eager"
              decoding="async"
            />
            <figcaption className="flex items-center justify-between gap-3 border-t border-line px-4 py-2.5 text-[10px] text-ink-faint">
              <span className="shrink-0">包装示意 · 服务端合成</span>
              <span className="min-w-0 truncate text-right">{trace.packaging.concept}</span>
            </figcaption>
          </figure>
        </div>

        <section className="mt-7 px-5">
          <div className="grid grid-cols-2 gap-2">
            {trace.timeline.slice(1).map((event, index) => (
              <div key={event.step} className="rounded-control border border-line bg-surface px-3 py-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] tabular-nums text-ink-faint">0{index + 1}</span>
                  <ShieldCheck size={12} className="text-leaf" />
                </div>
                <div className="mt-1.5 text-xs font-medium text-ink">{event.step}</div>
                <div className="mt-0.5 truncate text-[10px] text-ink-faint">{event.note}</div>
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] leading-6 text-ink-faint">
            四个 Agent 产出均经人工审核；区域事实引用知识库，品牌与角色为演示合成。
          </p>
        </section>

        <section className="mt-8 px-5">
          <SectionHeading
            eyebrow="STORY / IP"
            title={`${trace.story.ip_name} 看过的园子`}
            note={trace.story.persona}
          />
          <blockquote className="mt-4 border-l-2 border-apple pl-4 font-display text-xl leading-9 text-ink">
            {trace.story.story_short}
          </blockquote>
          <p className="mt-4 whitespace-pre-line break-words text-[15px] leading-8 text-ink-muted">
            {trace.story.story_long}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {trace.story.taglines.map((tagline) => (
              <span
                key={tagline}
                className="rounded-full border border-line bg-surface px-3 py-1 text-[11px] text-ink-muted"
              >
                {tagline}
              </span>
            ))}
          </div>
          <EvidenceList items={trace.story.evidence} />
        </section>

        <section className="mt-8 px-5">
          <SectionHeading
            eyebrow="PACKAGING"
            title="盒子上的话"
            note={trace.packaging.concept}
          />
          <div className="mt-4 rounded-card border border-line bg-surface-2/60 px-4 py-4">
            <CopyRow label="正面" text={trace.packaging.packaging_copy.front} emphasis />
            <CopyRow label="背面" text={trace.packaging.packaging_copy.back} />
            <CopyRow label="侧面" text={trace.packaging.packaging_copy.side} />
            <CopyRow label="盒内" text={trace.packaging.packaging_copy.inside} />
          </div>
          <dl className="mt-3 grid grid-cols-1 gap-2 text-xs">
            {Object.entries(trace.packaging.structure).map(([key, value]) => (
              <div key={key} className="flex gap-3 border-b border-line/60 pb-2 last:border-0">
                <dt className="w-16 shrink-0 text-ink-faint">{key}</dt>
                <dd className="min-w-0 break-words text-ink-muted">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="mt-8 px-5">
          <SectionHeading eyebrow="JOURNEY" title="这箱苹果的旅程" />
          <Timeline events={trace.journey} />
          <details className="group mt-4 rounded-card border border-line bg-surface">
            <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-xs text-ink">
              <span>审核记录</span>
              <ChevronDown size={14} className="text-ink-faint transition group-open:rotate-180" />
            </summary>
            <div className="border-t border-line px-4 py-2">
              <Timeline events={trace.timeline} withTime />
            </div>
          </details>
        </section>

        <section className="mt-8 px-5">
          <SectionHeading
            eyebrow="PRICE / TRACE"
            title="溢价从哪里来"
            note="价格、成本与溢价均为演示测算，不是市场报价或增收承诺。"
          />
          <div className="mt-4 rounded-card bg-ink p-5 text-paper">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-paper/50">
                  品牌礼盒目标价 · 演示
                </div>
                <div className="mt-2 font-display text-[40px] leading-none tabular-nums">
                  ¥{gift?.price_total ?? 0}
                  <span className="ml-1 text-xs font-normal text-paper/55">
                    / {gift?.pack ?? trace.product.form}
                  </span>
                </div>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full bg-apple px-3 py-1.5 text-xs tabular-nums text-white">
                <BadgePercent size={13} />
                溢价 {formatPct(trace.pricing.premium_pct)}
              </span>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-2">
              {trace.pricing.price_ladder.map((tier) => (
                <div key={tier.channel} className="rounded-control bg-paper/8 px-2.5 py-2.5">
                  <div className="text-[10px] text-paper/50">{tier.channel}</div>
                  <div className="mt-1 text-sm tabular-nums text-paper">¥{tier.price_total}</div>
                  <div className="mt-0.5 text-[9px] text-paper/40">{tier.pack}</div>
                </div>
              ))}
            </div>
          </div>
          <p className="mt-3 text-sm leading-7 text-ink-muted">{trace.pricing.rationale}</p>

          <details className="group mt-3 rounded-card border border-line bg-surface">
            <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-xs text-ink">
              <span>价格公式</span>
              <ChevronDown size={14} className="text-ink-faint transition group-open:rotate-180" />
            </summary>
            <p className="border-t border-line px-4 py-3 text-xs leading-7 text-ink-muted">
              {trace.pricing.formula}
            </p>
          </details>

          <details className="group mt-2 rounded-card border border-line bg-surface">
            <summary className="flex cursor-pointer list-none items-center justify-between px-4 py-3 text-xs text-ink">
              <span>成本构成（每 kg，演示）</span>
              <ChevronDown size={14} className="text-ink-faint transition group-open:rotate-180" />
            </summary>
            <div className="space-y-2.5 border-t border-line px-4 py-4">
              {Object.entries(trace.pricing.cost_breakdown).map(([label, value]) => (
                <div key={label} className="grid grid-cols-[64px_minmax(0,1fr)_48px] items-center gap-2 text-[11px]">
                  <span className="text-ink-muted">{label}</span>
                  <span className="h-1.5 overflow-hidden rounded-full bg-surface-2">
                    <span
                      className="block h-full rounded-full bg-kraft"
                      style={{ width: `${Math.max(4, (value / costMax) * 100)}%` }}
                    />
                  </span>
                  <span className="text-right tabular-nums text-ink">¥{value.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </details>
        </section>

        <section className="mt-8 px-5">
          <SectionHeading eyebrow="CONTENT" title="这一批，被这样介绍" />
          <article className="mt-4 rounded-card border border-line bg-surface p-5">
            <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.18em] text-ink-faint">
              <Sparkles size={12} className="text-apple" />
              小红书 · {trace.marketing.xiaohongshu.cover_text}
            </div>
            <h3 className="mt-2 font-display text-2xl leading-snug text-ink">
              {trace.marketing.xiaohongshu.title}
            </h3>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {trace.marketing.xiaohongshu.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-surface-2 px-2 py-0.5 text-[10px] text-ink-muted">
                  {tag}
                </span>
              ))}
            </div>
            <details className="group mt-3">
              <summary className="flex cursor-pointer list-none items-center gap-1 text-[11px] text-leaf">
                展开正文
                <ChevronDown size={12} className="transition group-open:rotate-180" />
              </summary>
              <p className="mt-2 whitespace-pre-line break-words text-xs leading-7 text-ink-muted">
                {trace.marketing.xiaohongshu.body}
              </p>
            </details>
          </article>
          <p className="mt-2 break-words text-[11px] leading-6 text-ink-faint">
            抖音钩子：{trace.marketing.douyin_hook}
          </p>
        </section>

        <section className="mt-8 px-5">
          <SectionHeading
            eyebrow="ASK THE ORCHARD"
            title="问守园人"
            note="演示对话。只回答这一批有记录的事，不编功效、认证或价格。"
          />
          <div className="mt-4 space-y-3" aria-live="polite">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[86%] break-words rounded-card px-4 py-3 text-[13px] leading-6 ${
                    message.role === "user"
                      ? "rounded-br-md bg-apple text-white"
                      : "rounded-bl-md border border-line bg-surface text-ink-muted"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="mb-1 flex items-center gap-1.5 text-[10px] text-ink-faint">
                      <MessageCircle size={11} />
                      {trace.story.ip_name}
                    </div>
                  )}
                  <p className="whitespace-pre-line">{message.content}</p>
                </div>
              </div>
            ))}
            {busy && (
              <div className="flex justify-start">
                <div className="rounded-card rounded-bl-md border border-line bg-surface px-4 py-3 text-xs text-ink-faint">
                  守园人正在看记录…
                </div>
              </div>
            )}
            {chatError && (
              <div className="flex flex-wrap items-center gap-2 text-xs text-danger" role="alert">
                <span>{chatError}</span>
                {lastUserMessage && (
                  <button
                    type="button"
                    onClick={retryChat}
                    className="underline underline-offset-4"
                  >
                    重试
                  </button>
                )}
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {suggestions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => void sendMessage(question)}
                disabled={busy}
                className="rounded-full border border-line bg-surface px-3 py-1.5 text-[11px] text-ink-muted disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>

          <form
            className="sticky bottom-0 z-10 mt-4 flex items-center gap-2 border-t border-line bg-paper/95 py-3 backdrop-blur"
            style={{ paddingBottom: "max(0.75rem, env(safe-area-inset-bottom))" }}
            onSubmit={(event) => {
              event.preventDefault();
              void sendMessage(input);
            }}
          >
            <label className="sr-only" htmlFor="trace-chat-input">
              问守园人
            </label>
            <input
              id="trace-chat-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              maxLength={300}
              enterKeyHint="send"
              autoComplete="off"
              placeholder="问产地、包装、价格或保存"
              className="min-w-0 flex-1 rounded-full border border-line bg-surface px-4 py-3 text-[16px] text-ink outline-none placeholder:text-ink-faint focus:border-apple/50"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              aria-label="发送问题"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-apple text-white disabled:opacity-40"
            >
              <Send size={17} />
            </button>
          </form>
        </section>

        <footer className="mt-6 px-5 pb-8 text-[11px] leading-6 text-ink-faint">
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line pt-4">
            <span className="inline-flex items-center gap-1.5 tabular-nums">
              <QrCode size={12} />
              本码已扫 {scanCount} 次
            </span>
            <span>{trace.fixed_demo ? "固定演示批次" : "演示批次"}</span>
          </div>
          <p className="mt-2">
            「{trace.product.brand_name}」与「{trace.story.ip_name}」为演示品牌与角色；区域事实可查，
            价格与成本为演示测算。
          </p>
          <Link to="/" className="mt-2 inline-block text-ink-muted underline underline-offset-4">
            进入桌面沙盘
          </Link>
        </footer>
      </div>
    </div>
  );
}
