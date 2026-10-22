import type { Batch } from "./client";

export type AgentKey = "story" | "packaging" | "marketing" | "pricing";
export type ArtifactKind = AgentKey | "illustration";

export interface BatchFull extends Batch {
  story_json: Record<string, unknown> | null;
  packaging_json: Record<string, unknown> | null;
  marketing_json: Record<string, unknown> | null;
  pricing_json: Record<string, unknown> | null;
}

export interface GuardIssue {
  rule: string;
  field: string;
  message: string;
  severity: "error" | "warning";
  suggestion: string;
}

export interface GuardResult {
  passed: boolean;
  checked_citations: number;
  errors: GuardIssue[];
  warnings: GuardIssue[];
}

export interface AgentRun {
  id: number;
  batch_id: number;
  agent: AgentKey;
  status: string;
  note: string | null;
  output_json: Record<string, unknown> | null;
  guard_json: GuardResult | null;
  error: string | null;
  model: string | null;
  tokens: number;
  started_at: string | null;
  finished_at: string | null;
}

export interface Artifact {
  id: number;
  batch_id: number;
  kind: ArtifactKind;
  content_json: Record<string, unknown> | null;
  file_path: string | null;
  file_url: string | null;
  approved_at: string | null;
}

export interface BatchWorkspace {
  batch: BatchFull;
  runs: AgentRun[];
  artifacts: Artifact[];
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = `API ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // keep the status text
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export const pipelineApi = {
  workspace: (batchId: number) => request<BatchWorkspace>(`/batches/${batchId}/workspace`),
  start: (batchId: number) =>
    request<BatchWorkspace>(`/batches/${batchId}/pipeline/start`, { method: "POST" }),
  run: (batchId: number, agent: AgentKey, note?: string) =>
    request<BatchWorkspace>(`/batches/${batchId}/agents/${agent}/run`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),
  approve: (batchId: number, agent: AgentKey, output?: Record<string, unknown>) =>
    request<BatchWorkspace>(`/batches/${batchId}/agents/${agent}/approve`, {
      method: "POST",
      body: JSON.stringify({ output }),
    }),
  reject: (batchId: number, agent: AgentKey, note?: string) =>
    request<BatchWorkspace>(`/batches/${batchId}/agents/${agent}/reject`, {
      method: "POST",
      body: JSON.stringify({ note }),
    }),
};
