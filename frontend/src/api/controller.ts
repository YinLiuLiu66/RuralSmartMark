export interface ControllerMessage {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  action_json: Record<string, unknown> | null;
  created_at: string;
}

export interface ControllerDraft {
  product?: {
    slug?: string;
    name?: string;
    county?: string;
    province?: string;
    category?: string;
    form?: string;
  };
  docs?: unknown[];
  benchmarks?: unknown[];
  questions?: string[];
  warnings?: string[];
}

export interface PendingAction {
  id: string;
  kind: string;
  summary: string;
  agent?: string;
  note?: string;
}

export interface ControllerSession {
  id: number;
  product_id: number | null;
  batch_id: number | null;
  product_name?: string | null;
  batch_code?: string | null;
  batch_state?: string | null;
  draft_json: ControllerDraft | null;
  pending_action_json: PendingAction | null;
  messages: ControllerMessage[];
  created_at: string;
  updated_at: string;
}

export interface ControllerTurn {
  session: ControllerSession;
  reply: string;
  questions: string[];
  pending_action: PendingAction | null;
  events: Record<string, unknown>[];
  thinking: string[];
}

export type ControllerStreamEvent =
  | { type: "user"; message: ControllerMessage }
  | { type: "thinking"; text: string }
  | { type: "delta"; text: string }
  | { type: "tool"; name: string; status: "running" | "done" }
  | { type: "done"; turn: ControllerTurn }
  | { type: "error"; detail: string };

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
      // keep status text
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

async function streamRequest(
  path: string,
  body: unknown,
  onEvent: (event: ControllerStreamEvent) => void,
): Promise<void> {
  const response = await fetch(`/api${path}`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = `API ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // keep status text
    }
    throw new Error(detail);
  }
  if (!response.body) throw new Error("当前浏览器不支持流式响应");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  function findBoundary(text: string): { index: number; length: number } | null {
    const match = /\r?\n\r?\n/.exec(text);
    return match ? { index: match.index, length: match[0].length } : null;
  }

  function dispatch(block: string) {
    for (const rawLine of block.split("\n")) {
      const line = rawLine.replace(/\r$/, "");
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (!payload) continue;
      try {
        onEvent(JSON.parse(payload) as ControllerStreamEvent);
      } catch {
        // 单个坏事件不终止整条流
      }
    }
  }

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary = findBoundary(buffer);
    while (boundary) {
      dispatch(buffer.slice(0, boundary.index));
      buffer = buffer.slice(boundary.index + boundary.length);
      boundary = findBoundary(buffer);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) dispatch(buffer);
}

export const controllerApi = {
  createSession: (
    productSlug?: string | null,
    batchId?: number | null,
    fresh = false,
    signal?: AbortSignal,
  ) =>
    request<ControllerSession>("/controller/sessions", {
      method: "POST",
      signal,
      body: JSON.stringify({
        product_slug: productSlug ?? null,
        batch_id: batchId ?? null,
        fresh,
      }),
    }),
  getSession: (sessionId: number) =>
    request<ControllerSession>(`/controller/sessions/${sessionId}`),
  sendMessage: (sessionId: number, message: string) =>
    request<ControllerTurn>(`/controller/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  streamMessage: (
    sessionId: number,
    message: string,
    onEvent: (event: ControllerStreamEvent) => void,
  ) =>
    streamRequest(`/controller/sessions/${sessionId}/messages/stream`, { message }, onEvent),
  confirm: (
    sessionId: number,
    actionId: string,
    decision: "confirm" | "cancel",
  ) =>
    request<ControllerTurn>(`/controller/sessions/${sessionId}/confirm`, {
      method: "POST",
      body: JSON.stringify({ action_id: actionId, decision }),
    }),
};
