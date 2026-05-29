import type {
  BatchRun,
  Brand,
  CreateBrandPayload,
  CreateBrandResponse,
  NormalizedFact,
  PromptRun,
  RankedTriggersExport,
  SourcePage,
  TriggerDecision,
} from "../types/contracts";

const ingestionBase =
  import.meta.env.VITE_INGESTION_API_URL ?? "http://127.0.0.1:8001";
const analysisBase =
  import.meta.env.VITE_ANALYSIS_API_URL ?? "http://127.0.0.1:8002";
const useMock = import.meta.env.VITE_USE_MOCK === "true";

async function request<T>(
  url: string,
  init?: RequestInit
): Promise<{ data: T; status: number }> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text();
    let message = `${res.status} ${res.statusText}`;
    try {
      const body = JSON.parse(text) as { detail?: string };
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      if (text) message = text;
    }
    throw new Error(message);
  }
  if (res.status === 204) {
    return { data: undefined as T, status: res.status };
  }
  return { data: (await res.json()) as T, status: res.status };
}

async function get<T>(url: string): Promise<T> {
  const { data } = await request<T>(url);
  return data;
}

async function getOptional<T>(url: string): Promise<T | null> {
  const res = await fetch(url);
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const { data } = await request<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return data;
}

const emptyExport = (brandId: string): RankedTriggersExport => ({
  brand_id: brandId,
  batch_run_id: "",
  scoring_config_version: "",
  generated_at: "",
  triggers: [],
});

export const api = {
  health: async () => {
    const [ingestion, analysis] = await Promise.all([
      get<{ status: string }>(`${ingestionBase}/health`),
      get<{ status: string }>(`${analysisBase}/health`),
    ]);
    return { ingestion, analysis };
  },

  listBrands: () =>
    useMock ? Promise.resolve(mockBrands) : get<Brand[]>(`${ingestionBase}/brands`),

  getBrand: (brandId: string) =>
    useMock
      ? Promise.resolve(mockBrands[0])
      : get<Brand>(`${ingestionBase}/brands/${brandId}`),

  createBrand: (payload: CreateBrandPayload) =>
    useMock
      ? Promise.resolve({
          brand_id: mockBrands[0].brand_id,
          status: "accepted",
          ingestion: "started",
        } as CreateBrandResponse)
      : post<CreateBrandResponse>(`${ingestionBase}/brands`, {
          ...payload,
          run_ingestion: payload.run_ingestion ?? true,
        }),

  getIngestionBatchRun: (brandId: string) =>
    useMock
      ? Promise.resolve(mockIngestionBatch(brandId))
      : getOptional<BatchRun>(`${ingestionBase}/brands/${brandId}/batch-run`),

  getAnalysisBatchRun: (brandId: string) =>
    useMock
      ? Promise.resolve(null)
      : getOptional<BatchRun>(`${analysisBase}/brands/${brandId}/batch-run`),

  startAnalysis: (brandId: string) =>
    useMock
      ? Promise.resolve({ brand_id: brandId, status: "accepted" })
      : post<{ brand_id: string; status: string }>(
          `${analysisBase}/brands/${brandId}/analyze`,
          {}
        ),

  getFacts: (brandId: string) =>
    useMock
      ? Promise.resolve([])
      : get<NormalizedFact[]>(`${ingestionBase}/brands/${brandId}/facts`),

  getSourcePages: (brandId: string) =>
    useMock
      ? Promise.resolve([])
      : get<SourcePage[]>(`${ingestionBase}/brands/${brandId}/source-pages`),

  getPromptRuns: (brandId: string) =>
    useMock
      ? Promise.resolve([])
      : get<PromptRun[]>(`${analysisBase}/brands/${brandId}/prompt-runs`),

  getTriggers: async (brandId: string) => {
    if (useMock) return mockExport(brandId);
    const data = await getOptional<RankedTriggersExport>(
      `${analysisBase}/brands/${brandId}/triggers`
    );
    return data ?? emptyExport(brandId);
  },

  saveDecision: async (decision: TriggerDecision) => {
    const key = `decisions:${decision.brand_id}`;
    const existing = JSON.parse(localStorage.getItem(key) ?? "[]");
    existing.push(decision);
    localStorage.setItem(key, JSON.stringify(existing));
  },
};

const mockBrands: Brand[] = [
  {
    brand_id: "00000000-0000-4000-8000-000000000001",
    name: "Acme Analytics",
    primary_domain: "acme-analytics.example",
    competitor_domains: [],
    seed_topics: [],
    created_at: "2026-05-28T12:00:00Z",
  },
];

function mockIngestionBatch(brandId: string): BatchRun {
  return {
    batch_run_id: "mock-ingest",
    brand_id: brandId,
    run_type: "ingestion",
    status: "completed",
    started_at: new Date().toISOString(),
    finished_at: new Date().toISOString(),
    stats: { source_pages: 3, normalized_facts: 3 },
    errors: [],
  };
}

function mockExport(brandId: string): RankedTriggersExport {
  return {
    brand_id: brandId,
    batch_run_id: "mock-batch",
    scoring_config_version: "1.0.0",
    generated_at: new Date().toISOString(),
    triggers: [
      {
        trigger_candidate_id: "t1",
        brand_id: brandId,
        batch_run_id: "mock-batch",
        phrase: "product analytics",
        phrase_type: "bigram",
        intent_bucket: "commercial_investigation",
        appearance_count: 12,
        appearance_rate: 0.4,
        trigger_score: 0.82,
        recommended_action: "prioritize",
      },
    ],
  };
}
