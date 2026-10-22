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
      // keep status text
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const controllerApi = {
  createSession: (productSlug?: string | null, batchId?: number | null) =>
    request<ControllerSession>("/controller/sessions", {
      method: "POST",
      body: JSON.stringify({
        product_slug: productSlug ?? null,
        batch_id: batchId ?? null,
      }),
    }),
  sendMessage: (sessionId: number, message: string) =>
    request<ControllerTurn>(`/controller/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
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
