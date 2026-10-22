import { create } from "zustand";

import type { Batch, Product } from "../api/client";

interface WorldState {
  products: Product[];
  selectedProductId: number | null;
  batches: Batch[];
  selectedBatchId: number | null;
  setProducts: (products: Product[]) => void;
  selectProduct: (id: number | null) => void;
  setBatches: (batches: Batch[]) => void;
  selectBatch: (id: number | null) => void;
}

export const useWorldStore = create<WorldState>((set) => ({
  products: [],
  selectedProductId: null,
  batches: [],
  selectedBatchId: null,
  setProducts: (products) =>
    set((state) => ({
      products,
      selectedProductId:
        state.selectedProductId ?? products[0]?.id ?? null,
    })),
  selectProduct: (selectedProductId) =>
    set({ selectedProductId, selectedBatchId: null }),
  setBatches: (batches) =>
    set((state) => {
      const visible = state.selectedProductId
        ? batches.filter((batch) => batch.product_id === state.selectedProductId)
        : batches;
      const current = visible.find((batch) => batch.id === state.selectedBatchId);
      return {
        batches,
        selectedBatchId:
          current?.id ??
          visible.find((batch) => batch.code === "ZT-DEMO-001")?.id ??
          visible.find((batch) => batch.state === "traced")?.id ??
          visible[0]?.id ??
          null,
      };
    }),
  selectBatch: (selectedBatchId) => set({ selectedBatchId }),
}));
