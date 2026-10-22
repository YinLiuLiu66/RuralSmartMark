export interface Product {
  id: number;
  slug: string;
  name: string;
  county: string;
  province: string;
  category: string;
  form: string;
  specs: Record<string, string>;
  palette: Record<string, string>;
  scene_preset: string;
  knowledge_dir: string;
  is_active: boolean;
}

export interface Batch {
  id: number;
  product_id: number;
  code: string;
  quantity_kg: number;
  state: string;
  current_station: string;
  trace_code: string | null;
  created_at: string;
  updated_at: string;
}

export interface Health {
  status: string;
  app: string;
  db: string;
}

export interface KnowledgeDoc {
  doc_key: string;
  title: string;
  type: string;
  source_url: string | null;
  source_date: string | null;
  credibility: string;
}

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`API ${response.status}: ${path}`);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => get<Health>("/health"),
  products: () => get<Product[]>("/products"),
  batches: () => get<Batch[]>("/batches"),
  knowledge: () => get<KnowledgeDoc[]>("/knowledge"),
};
