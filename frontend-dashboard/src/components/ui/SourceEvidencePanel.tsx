import { useEffect, useState } from "react";
import { api } from "../../api/client";
import type { PromptRun, SourcePage } from "../../types/contracts";

export function SourceEvidencePanel({
  brandId,
  sourcePageIds,
  promptRunIds,
}: {
  brandId: string;
  sourcePageIds: string[];
  promptRunIds: string[];
}) {
  const [pages, setPages] = useState<SourcePage[]>([]);
  const [runs, setRuns] = useState<PromptRun[]>([]);

  useEffect(() => {
    Promise.all([api.getSourcePages(brandId), api.getPromptRuns(brandId)]).then(
      ([allPages, allRuns]) => {
        setPages(
          allPages.filter((p) => sourcePageIds.includes(p.source_page_id))
        );
        setRuns(allRuns.filter((r) => promptRunIds.includes(r.prompt_run_id)));
      }
    );
  }, [brandId, sourcePageIds, promptRunIds]);

  return (
    <div className="card">
      <h3>Evidence</h3>
      <h4>Source pages ({pages.length})</h4>
      {pages.length === 0 ? (
        <p className="muted">No source pages linked.</p>
      ) : (
        <ul className="evidence-list">
          {pages.map((p) => (
            <li key={p.source_page_id}>
              <a href={p.url} target="_blank" rel="noreferrer">
                {p.title || p.url}
              </a>
              <span className="muted"> — {p.page_type}</span>
            </li>
          ))}
        </ul>
      )}
      <h4>Prompt runs ({runs.length})</h4>
      {runs.length === 0 ? (
        <p className="muted">No prompt runs linked.</p>
      ) : (
        <ul className="evidence-list">
          {runs.map((r) => (
            <li key={r.prompt_run_id}>
              <code>{r.prompt_run_id.slice(0, 8)}…</code>
              {r.response_text && (
                <p className="snippet">{r.response_text.slice(0, 200)}…</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
