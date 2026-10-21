import { Link, useParams } from "react-router-dom";

export default function Trace() {
  const { code = "" } = useParams();

  return (
    <div className="min-h-dvh bg-paper px-5 py-8 text-ink">
      <div className="mx-auto max-w-[430px]">
        <div className="text-[11px] uppercase tracking-[0.2em] text-ink-muted">
          乡土印记 · 溯源
        </div>
        <h1 className="mt-3 font-display text-3xl leading-tight">
          这箱苹果，
          <br />
          从乌蒙山来。
        </h1>
        <p className="mt-4 text-sm leading-7 text-ink-muted">
          溯源码 <span className="font-medium text-ink">{code || "未提供"}</span>。
          Phase 3 会在这里接入故事、时间线、价格和 IP 对话。
        </p>

        <div className="card mt-6 p-5">
          <div className="text-xs text-ink-muted">当前进度</div>
          <div className="mt-2 text-lg">溯源页骨架已就位</div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-2">
            <div className="h-full w-1/3 rounded-full bg-apple" />
          </div>
        </div>

        <Link
          to="/"
          className="mt-6 inline-block text-xs text-ink-muted underline underline-offset-4"
        >
          返回沙盘（桌面端）
        </Link>
      </div>
    </div>
  );
}
