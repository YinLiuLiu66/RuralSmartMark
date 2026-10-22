export interface TracePriceTier {
  channel: string;
  pack: string;
  price_per_kg: number;
  price_total: number;
  note: string;
}

export interface TraceQA {
  q: string;
  a: string;
}

export interface TraceEvidence {
  doc_id: string;
  title: string;
  source_url: string | null;
  source_date: string | null;
  credibility: string;
  quote: string;
  use: string | null;
}

export interface TraceTimelineEvent {
  step: string;
  note: string;
  at: string | null;
}

export interface Trace {
  trace_code: string;
  batch: {
    code: string;
    trace_code: string;
    quantity_kg: number;
    created_at: string;
  };
  product: {
    name: string;
    county: string;
    province: string;
    form: string;
    brand_name: string;
    ip_name: string;
    specs: Record<string, string>;
  };
  story: {
    ip_name: string;
    persona: string;
    story_long: string;
    story_short: string;
    taglines: string[];
    evidence: TraceEvidence[];
  };
  packaging: {
    concept: string;
    packaging_copy: {
      front: string;
      back: string;
      side: string;
      inside: string;
    };
    structure: Record<string, string>;
    image_url: string;
  };
  marketing: {
    xiaohongshu: {
      title: string;
      body: string;
      tags: string[];
      cover_text: string;
    };
    douyin_hook: string;
    wechat_title: string;
  };
  pricing: {
    price_ladder: TracePriceTier[];
    premium_pct: number;
    rationale: string;
    formula: string;
    cost_breakdown: Record<string, number>;
    faq: TraceQA[];
    persona_greeting: string;
    is_demo: boolean;
  };
  timeline: TraceTimelineEvent[];
  journey: TraceTimelineEvent[];
  scan_count: number;
  last_scanned_at: string | null;
  demo: boolean;
  fixed_demo: boolean;
}

export interface TraceScan {
  scan_count: number;
  recorded: boolean;
}

export interface TraceChat {
  reply: string;
  source: "llm" | "template";
}

export class TraceNotFoundError extends Error {
  constructor() {
    super("溯源码不存在");
    this.name = "TraceNotFoundError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    cache: "no-store",
    ...init,
    headers: {
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (response.status === 404) {
    throw new TraceNotFoundError();
  }
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }
  return (await response.json()) as T;
}

export const traceApi = {
  get: (code: string) => request<Trace>(`/trace/${encodeURIComponent(code)}`),
  scan: (code: string) =>
    request<TraceScan>(`/trace/${encodeURIComponent(code)}/scan`, { method: "POST" }),
  scanCount: (code: string) => request<TraceScan>(`/trace/${encodeURIComponent(code)}/scan`),
  chat: (code: string, message: string) =>
    request<TraceChat>(`/trace/${encodeURIComponent(code)}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
};
