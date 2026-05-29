import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { StatusBadge } from "../components/ui/StatusBadge";
import type { BatchRun } from "../types/contracts";

const TERMINAL = new Set(["completed", "failed", "partial"]);

export function RunStatusPage() {
  const { brandId = "" } = useParams();
  const [ingestion, setIngestion] = useState<BatchRun | null>(null);
  const [analysis, setAnalysis] = useState<BatchRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [startingAnalysis, setStartingAnalysis] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [ing, ana] = await Promise.all([
        api.getIngestionBatchRun(brandId),
        api.getAnalysisBatchRun(brandId),
      ]);
      setIngestion(ing);
      setAnalysis(ana);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [brandId]);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 2500);
    return () => window.clearInterval(id);
  }, [refresh]);

  const ingestionDone =
    ingestion?.status && TERMINAL.has(ingestion.status) && ingestion.status !== "failed";
  const analysisDone = analysis?.status && TERMINAL.has(analysis.status);

  const runAnalysis = async () => {
    setStartingAnalysis(true);
    setError(null);
    try {
      await api.startAnalysis(brandId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setStartingAnalysis(false);
    }
  };

  return (
    <div>
      <h1>Run status</h1>
      {error && <p className="error" role="alert">{error}</p>}

      <section className="card">
        <h2>Section 1 — Ingestion</h2>
        {ingestion ? (
          <>
            <p>
              Status: <StatusBadge status={ingestion.status} />
            </p>
            {ingestion.stats && (
              <pre className="stats">{JSON.stringify(ingestion.stats, null, 2)}</pre>
            )}
            {ingestion.errors && ingestion.errors.length > 0 && (
              <pre className="error">{JSON.stringify(ingestion.errors, null, 2)}</pre>
            )}
          </>
        ) : (
          <p>Waiting for ingestion batch metadata…</p>
        )}
      </section>

      <section className="card">
        <h2>Section 2 — Analysis</h2>
        {analysis ? (
          <>
            <p>
              Status: <StatusBadge status={analysis.status} />
            </p>
            {analysis.stats && (
              <pre className="stats">{JSON.stringify(analysis.stats, null, 2)}</pre>
            )}
          </>
        ) : (
          <p>No analysis run yet.</p>
        )}
        {ingestionDone && !analysisDone && (
          <button
            type="button"
            onClick={runAnalysis}
            disabled={startingAnalysis || analysis?.status === "running"}
          >
            {startingAnalysis ? "Starting…" : "Run analysis"}
          </button>
        )}
        {analysisDone && analysis?.status === "completed" && (
          <p>
            <Link to={`/brands/${brandId}/triggers`}>View ranked triggers →</Link>
          </p>
        )}
      </section>

      {ingestionDone && (
        <p>
          <Link to={`/brands/${brandId}/knowledge`}>Browse knowledge base →</Link>
        </p>
      )}
    </div>
  );
}
