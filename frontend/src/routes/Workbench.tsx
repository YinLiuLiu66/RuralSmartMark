import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MessageSquare, Plus, Sparkles, Sprout } from "lucide-react";

import { api, type Batch, type Product } from "../api/client";
import ProjectCard from "../components/workbench/ProjectCard";
import { useControllerStore } from "../stores/controller";
import { useWorldStore } from "../stores/world";

export default function Workbench() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const dataVersion = useControllerStore((state) => state.dataVersion);
  const setControllerOpen = useControllerStore((state) => state.setOpen);
  const setProducts = useWorldStore((state) => state.setProducts);
  const setBatches = useWorldStore((state) => state.setBatches);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([api.products(), api.batches()])
      .then(([products, batches]) => {
        if (cancelled) return;
        setProducts(products);
        setBatches(batches);
        setError(null);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "项目列表加载失败");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [dataVersion, setProducts, setBatches]);

  const products = useWorldStore((state) => state.products);
  const batches = useWorldStore((state) => state.batches);

  const byProduct = useMemo(() => {
    const map = new Map<number, Batch[]>();
    for (const batch of batches) {
      const list = map.get(batch.product_id) ?? [];
      list.push(batch);
      map.set(batch.product_id, list);
    }
    return map;
  }, [batches]);

  const empty = !loading && products.length === 0;

  return (
    <div className="min-h-dvh bg-paper">
      <header className="sticky top-0 z-20 border-b border-line bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-8">
          <div className="flex items-center gap-2">
            <Sprout size={18} className="text-apple" />
            <div>
              <div className="font-display text-lg leading-tight text-ink">智农云链</div>
              <p className="text-[10px] text-ink-faint">
                县域农产品品牌流水线 · 每个项目一条产线
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/controller"
              className="hidden h-8 items-center gap-1 rounded-control border border-line px-2.5 text-[11px] text-ink-muted hover:border-apple/40 hover:text-apple sm:flex"
            >
              <MessageSquare size={12} />
              全页聊天
            </Link>
            <button
              type="button"
              onClick={() => setControllerOpen(true)}
              className="flex h-8 items-center gap-1 rounded-control border border-line px-2.5 text-[11px] text-ink-muted hover:border-apple/40 hover:text-apple"
            >
              <Sparkles size={12} />
              总控
            </button>
            <button
              type="button"
              onClick={() => setControllerOpen(true)}
              className="flex h-8 items-center gap-1 rounded-control bg-apple px-2.5 text-[11px] font-medium text-white hover:bg-apple-hover"
            >
              <Plus size={12} />
              新建产品
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6 md:px-8 md:py-10">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-ink-faint">
              Projects
            </p>
            <h1 className="mt-1 font-display text-2xl text-ink md:text-3xl">我的项目</h1>
            <p className="mt-1 text-xs leading-6 text-ink-muted">
              点开任意项目进入 3D 沙盘；换产品只换档案、知识库、包装模板与基准价。
            </p>
          </div>
          {!loading && products.length > 0 && (
            <p className="text-[11px] text-ink-faint">
              {products.length} 个项目 · {batches.length} 个批次
            </p>
          )}
        </div>

        {loading && (
          <div className="mt-10 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[0, 1].map((index) => (
              <div
                key={index}
                className="card h-64 animate-pulse bg-surface/60"
                aria-hidden
              />
            ))}
          </div>
        )}

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-card border border-danger/30 bg-surface px-4 py-3 text-xs text-danger"
          >
            {error}；请确认后端已在 8000 端口启动。
          </div>
        )}

        {!loading && products.length > 0 && (
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {products.map((product: Product) => (
              <ProjectCard
                key={product.id}
                product={product}
                batches={byProduct.get(product.id) ?? []}
              />
            ))}
            <button
              type="button"
              onClick={() => setControllerOpen(true)}
              className="flex min-h-[16rem] flex-col items-center justify-center gap-2 rounded-card border border-dashed border-line bg-surface/50 p-6 text-center transition-colors hover:border-apple/40 hover:bg-apple-weak/20"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-full border border-dashed border-line-strong text-apple">
                <Plus size={18} />
              </span>
              <span className="font-display text-base text-ink">再加一个产品</span>
              <span className="max-w-[14rem] text-[11px] leading-5 text-ink-muted">
                告诉总控产品名、产地和品类；调研建档后，这里会多一张卡。
              </span>
            </button>
          </div>
        )}

        {empty && (
          <div className="mt-10 rounded-card border border-dashed border-line bg-surface p-8 text-center">
            <p className="text-[10px] uppercase tracking-[0.24em] text-ink-faint">
              还没有项目
            </p>
            <h2 className="mt-2 font-display text-2xl text-ink">先做一个产品</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-7 text-ink-muted">
              把产品名、产地和品类告诉总控，它会先调研来源，再生成产品档案与第一批次。
            </p>
            <button
              type="button"
              onClick={() => setControllerOpen(true)}
              className="mt-5 rounded-control bg-apple px-4 py-2 text-xs font-medium text-white hover:bg-apple-hover"
            >
              打开总控
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
