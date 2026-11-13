import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, QrCode } from "lucide-react";

import type { Batch, Product } from "../../api/client";
import { STATE_STAGE, STATUS_LABEL } from "../../agents";

function pickLatest(batches: Batch[]): Batch | null {
  if (batches.length === 0) return null;
  const traced = batches.find((batch) => batch.state === "traced");
  if (traced) return traced;
  return [...batches].sort((a, b) => b.updated_at.localeCompare(a.updated_at))[0];
}

export default function ProjectCard({
  product,
  batches,
}: {
  product: Product;
  batches: Batch[];
}) {
  const [thumbFailed, setThumbFailed] = useState(false);
  const latest = pickLatest(batches);
  const stage = latest ? (STATE_STAGE[latest.state] ?? 0) : 0;
  const palette = product.palette ?? {};
  const accent = palette.apple ?? "#b6402a";

  const thumbSrc = (() => {
    if (!latest) return null;
    if (latest.state === "traced" && latest.trace_code) {
      return `/api/trace/${latest.trace_code}/packaging.png`;
    }
    if (stage >= 2) {
      return `/api/batches/${latest.id}/agents/packaging/preview?variant=kraft`;
    }
    return null;
  })();

  const href = `/project/${product.slug}${latest ? `?batch=${latest.id}` : ""}`;

  return (
    <Link
      to={href}
      className="card group flex flex-col overflow-hidden transition-shadow hover:shadow-[0_2px_4px_rgb(31_42_36/0.08),0_16px_40px_rgb(31_42_36/0.12)]"
    >
      <div
        className="relative flex h-36 items-center justify-center overflow-hidden border-b border-line"
        style={{
          background: `linear-gradient(135deg, ${palette.paper ?? "#f7f3ea"} 0%, ${
            palette.kraft ?? "#c9a46a"
          }33 100%)`,
        }}
      >
        {thumbSrc && !thumbFailed ? (
          <img
            src={thumbSrc}
            alt={`${product.name} 包装`}
            loading="lazy"
            onError={() => setThumbFailed(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center gap-1">
            <span
              className="font-display text-4xl"
              style={{ color: accent }}
              aria-hidden
            >
              {product.name.slice(0, 1)}
            </span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-ink-faint">
              {product.category}
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate font-display text-lg text-ink">{product.name}</h3>
            <p className="mt-0.5 truncate text-[11px] text-ink-muted">
              {product.county} · {product.form}
            </p>
          </div>
          <span
            className="shrink-0 rounded-full border px-2 py-0.5 text-[10px]"
            style={{ borderColor: `${accent}55`, color: accent }}
          >
            {latest ? (STATUS_LABEL[latest.state] ?? latest.state) : "还没有批次"}
          </span>
        </div>

        <div className="mt-auto space-y-2 pt-1">
          <div className="flex items-center justify-between gap-2 text-[10px] text-ink-faint">
            <span className="flex min-w-0 items-center gap-1.5">
              <span className="truncate">{latest ? latest.code : "未创建批次"}</span>
              {latest?.trace_code && (
                <span className="flex shrink-0 items-center gap-0.5 text-leaf">
                  <QrCode size={9} />
                  {latest.trace_code}
                </span>
              )}
            </span>
            <span className="shrink-0">{stage}/6 站</span>
          </div>
          <div className="h-1 overflow-hidden rounded-full bg-line">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${(stage / 6) * 100}%`, background: accent }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-ink-muted">
            <span>{batches.length} 个批次</span>
            <span className="flex items-center gap-1 text-apple opacity-0 transition-opacity group-hover:opacity-100">
              进入沙盘
              <ArrowRight size={11} />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
