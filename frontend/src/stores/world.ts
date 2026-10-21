import { create } from "zustand";

import type { Batch } from "../api/client";

interface WorldState {
  batches: Batch[];
  selectedBatchId: number | null;
  setBatches: (batches: Batch[]) => void;
  selectBatch: (id: number | null) => void;
}

export const useWorldStore = create<WorldState>((set) => ({
  batches: [],
  selectedBatchId: null,
  setBatches: (batches) =>
    set({ batches, selectedBatchId: batches[0]?.id ?? null }),
  selectBatch: (selectedBatchId) => set({ selectedBatchId }),
}));
