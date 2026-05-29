import { defineConfig, mergeConfig } from "vitest/config";
import viteConfig from "./vite.config";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "node",
      env: {
        VITE_USE_MOCK: "false",
        VITE_INGESTION_API_URL: "http://ingestion.test",
        VITE_ANALYSIS_API_URL: "http://analysis.test",
      },
    },
  })
);
