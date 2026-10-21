import { create } from "zustand";

import { pipelineApi, type AgentKey, type BatchWorkspace } from "../api/pipeline";

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败";
}

interface PipelineState {
  workspace: BatchWorkspace | null;
  selectedAgent: AgentKey | null;
  busy: boolean;
  error: string | null;
  setWorkspace: (workspace: BatchWorkspace | null) => void;
  selectAgent: (agent: AgentKey | null) => void;
  refresh: (batchId: number, quiet?: boolean) => Promise<BatchWorkspace | null>;
  start: (batchId: number) => Promise<BatchWorkspace | null>;
  run: (batchId: number, agent: AgentKey, note?: string) => Promise<BatchWorkspace | null>;
  approve: (
    batchId: number,
    agent: AgentKey,
    output?: Record<string, unknown>,
  ) => Promise<BatchWorkspace | null>;
  reject: (batchId: number, agent: AgentKey, note?: string) => Promise<BatchWorkspace | null>;
}

export const usePipelineStore = create<PipelineState>((set) => {
  async function perform(
    request: () => Promise<BatchWorkspace>,
  ): Promise<BatchWorkspace> {
    set({ busy: true, error: null });
    try {
      const workspace = await request();
      set({ workspace, busy: false });
      return workspace;
    } catch (error) {
      set({ busy: false, error: errorMessage(error) });
      throw error;
    }
  }

  return {
    workspace: null,
    selectedAgent: null,
    busy: false,
    error: null,
    setWorkspace: (workspace) => set({ workspace }),
    selectAgent: (selectedAgent) => set({ selectedAgent }),
    refresh: async (batchId, quiet = false) => {
      if (quiet) {
        try {
          const workspace = await pipelineApi.workspace(batchId);
          set({ workspace, error: null });
          return workspace;
        } catch {
          return null;
        }
      }
      return perform(() => pipelineApi.workspace(batchId));
    },
    start: (batchId) => perform(() => pipelineApi.start(batchId)),
    run: (batchId, agent, note) => perform(() => pipelineApi.run(batchId, agent, note)),
    approve: (batchId, agent, output) =>
      perform(() => pipelineApi.approve(batchId, agent, output)),
    reject: (batchId, agent, note) => perform(() => pipelineApi.reject(batchId, agent, note)),
  };
});
