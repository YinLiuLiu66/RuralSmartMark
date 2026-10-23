import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, type Batch, type Product } from "../api/client";
import ControllerPanel from "../components/ControllerPanel";

export default function Controller() {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [productSlug, setProductSlug] = useState<string | null>(null);
  const [batchId, setBatchId] = useState<number | null>(null);
  const [freshToken, setFreshToken] = useState<number | undefined>(undefined);

  async function load(selectNewest = false) {
    const [productList, batchList] = await Promise.all([api.products(), api.batches()]);
    setProducts(productList);
    setBatches(batchList);
    const product = selectNewest
      ? productList[productList.length - 1] ?? null
      : productList[0] ?? null;
    setProductSlug(product?.slug ?? null);
    const visible = product
      ? batchList.filter((batch) => batch.product_id === product.id)
      : batchList;
    setBatchId(visible[0]?.id ?? null);
  }

  useEffect(() => {
    void load(false);
  }, []);

  return (
    <div className="min-h-dvh bg-paper">
      <ControllerPanel
        inline
        productSlug={freshToken !== undefined ? null : productSlug}
        batchId={freshToken !== undefined ? null : batchId}
        freshToken={freshToken}
        onNewProduct={() => setFreshToken(Date.now())}
        onClose={() => navigate("/")}
        onDataChanged={() => void load(true)}
      />
      {products.length === 0 && batches.length === 0 && (
        <div className="mx-auto max-w-[720px] px-6 py-4 text-center text-xs text-ink-faint">
          还没有产品；在总控里说“帮我做一个新产品”即可开始。
        </div>
      )}
    </div>
  );
}
