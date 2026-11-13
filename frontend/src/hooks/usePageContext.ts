import { matchPath, useLocation } from "react-router-dom";

import type { ControllerPageContext } from "../api/controller";
import { useWorldStore } from "../stores/world";

export interface PageContext extends ControllerPageContext {
  productName: string | null;
  batchCode: string | null;
  batchState: string | null;
}

/** 页面上下文从 URL 派生，不做可写 store，避免切页后残留旧批次。 */
export function usePageContext(): PageContext {
  const { pathname, search } = useLocation();
  const products = useWorldStore((state) => state.products);
  const batches = useWorldStore((state) => state.batches);
  const params = new URLSearchParams(search);

  const projectMatch = matchPath("/project/:slug", pathname);
  const slug = projectMatch?.params.slug ?? null;
  const product = slug ? (products.find((item) => item.slug === slug) ?? null) : null;
  const rawBatchId = Number(params.get("batch"));
  const batchId = Number.isFinite(rawBatchId) && rawBatchId > 0 ? rawBatchId : null;
  const batch = batchId ? (batches.find((item) => item.id === batchId) ?? null) : null;

  const route = projectMatch
    ? "project"
    : pathname === "/controller"
      ? "controller"
      : "workbench";

  return {
    route,
    product_slug: product?.slug ?? slug,
    batch_id: batch?.id ?? batchId,
    focus_agent: params.get("station"),
    productName: product?.name ?? null,
    batchCode: batch?.code ?? null,
    batchState: batch?.state ?? null,
  };
}

export function toApiContext(context: PageContext): ControllerPageContext {
  return {
    route: context.route ?? null,
    product_slug: context.product_slug ?? null,
    batch_id: context.batch_id ?? null,
    focus_agent: context.focus_agent ?? null,
  };
}
