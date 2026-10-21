import type { AgentKey, AgentRun, BatchFull, BatchWorkspace } from "./api/pipeline";

export type StationStatus = "idle" | "running" | "review" | "done" | "failed";

export interface AgentMeta {
  key: AgentKey;
  name: string;
  short: string;
  stationId: string;
  color: string;
}

export const AGENTS: AgentMeta[] = [
  { key: "story", name: "故事 / IP", short: "故事", stationId: "story", color: "#C9A46A" },
  { key: "packaging", name: "包装设计", short: "包装", stationId: "packaging", color: "#B6402A" },
  { key: "marketing", name: "内容营销", short: "内容", stationId: "marketing", color: "#3F6B4F" },
  { key: "pricing", name: "定价 / 溯源", short: "定价", stationId: "warehouse", color: "#8A8578" },
];

export const AGENT_BY_KEY = Object.fromEntries(
  AGENTS.map((agent) => [agent.key, agent]),
) as Record<AgentKey, AgentMeta>;

export const AGENT_BY_STATION = Object.fromEntries(
  AGENTS.map((agent) => [agent.stationId, agent]),
) as Record<string, AgentMeta>;

export const AGENT_FIELD: Record<
  AgentKey,
  "story_json" | "packaging_json" | "marketing_json" | "pricing_json"
> = {
  story: "story_json",
  packaging: "packaging_json",
  marketing: "marketing_json",
  pricing: "pricing_json",
};

const READY_STATE: Record<AgentKey, string> = {
  story: "raw",
  packaging: "story_approved",
  marketing: "packaging_approved",
  pricing: "marketing_approved",
};

export function nextAgent(state: string): AgentKey | null {
  for (const agent of AGENTS) {
    if (state === READY_STATE[agent.key]) return agent.key;
  }
  return null;
}

export function reviewAgent(state: string): AgentKey | null {
  if (!state.endsWith("_review")) return null;
  const key = state.slice(0, -"_review".length);
  return key in AGENT_BY_KEY ? (key as AgentKey) : null;
}

export const STATE_STAGE: Record<string, number> = {
  raw: 0,
  story_running: 1,
  story_review: 1,
  story_approved: 1,
  packaging_running: 2,
  packaging_review: 2,
  packaging_approved: 2,
  marketing_running: 3,
  marketing_review: 3,
  marketing_approved: 3,
  pricing_running: 4,
  pricing_review: 4,
  pricing_approved: 4,
  traced: 5,
  shipped: 5,
};

export const STATUS_LABEL: Record<string, string> = {
  raw: "原料待处理",
  story_running: "故事生成中",
  story_review: "故事待审核",
  story_approved: "故事已定稿",
  packaging_running: "包装生成中",
  packaging_review: "包装待审核",
  packaging_approved: "包装已定稿",
  marketing_running: "内容生成中",
  marketing_review: "内容待审核",
  marketing_approved: "内容已定稿",
  pricing_running: "定价测算中",
  pricing_review: "定价待审核",
  pricing_approved: "定价已定稿",
  traced: "已溯源",
  shipped: "已出库",
};

export const RUN_STATUS_LABEL: Record<StationStatus, string> = {
  idle: "待运行",
  running: "生成中",
  review: "待审核",
  done: "已通过",
  failed: "失败",
};

export const RUN_STATUS_STYLE: Record<StationStatus, string> = {
  idle: "border-line text-ink-muted",
  running: "border-apple/30 bg-apple-weak text-apple",
  review: "border-amber/30 bg-amber/10 text-amber",
  done: "border-leaf/30 bg-leaf-weak text-leaf",
  failed: "border-danger/30 bg-apple-weak text-danger",
};

export function latestRun(
  workspace: BatchWorkspace | null,
  agent: AgentKey,
): AgentRun | null {
  return workspace?.runs.find((run) => run.agent === agent) ?? null;
}

export function agentStatus(
  workspace: BatchWorkspace | null,
  agent: AgentKey,
): StationStatus {
  const run = latestRun(workspace, agent);
  if (run) {
    if (run.status === "running") return "running";
    if (run.status === "waiting_review") return "review";
    if (run.status === "approved") return "done";
    if (run.status === "failed") return "failed";
  }
  return "idle";
}

export type AgentOutput = Record<string, unknown> | null;

export function outputForAgent(
  workspace: BatchWorkspace | null,
  agent: AgentKey,
): AgentOutput {
  const run = latestRun(workspace, agent);
  if (run?.output_json) return run.output_json;
  const batch = workspace?.batch as BatchFull | undefined;
  return (batch?.[AGENT_FIELD[agent]] as Record<string, unknown> | null) ?? null;
}
