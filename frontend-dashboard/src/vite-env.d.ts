/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_INGESTION_API_URL: string;
  readonly VITE_ANALYSIS_API_URL: string;
  readonly VITE_USE_MOCK: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
