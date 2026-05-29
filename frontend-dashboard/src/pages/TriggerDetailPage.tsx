import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { SourceEvidencePanel } from "../components/ui/SourceEvidencePanel";
import type { TriggerCandidate, TriggerDecisionType } from "../types/contracts";

export function TriggerDetailPage() {
  const { brandId = "", triggerId = "" } = useParams();
  const [trigger, setTrigger] = useState<TriggerCandidate | null>(null);

  useEffect(() => {
    api.getTriggers(brandId).then((exp) => {
      setTrigger(exp.triggers.find((t) => t.trigger_candidate_id === triggerId) ?? null);
    });
  }, [brandId, triggerId]);

  const decide = (decision: TriggerDecisionType) => {
    if (!trigger) return;
    api.saveDecision({
      trigger_decision_id: crypto.randomUUID(),
      trigger_candidate_id: trigger.trigger_candidate_id,
      brand_id: brandId,
      decision,
      decided_at: new Date().toISOString(),
    });
  };

  if (!trigger) return <p>Loading…</p>;

  return (
    <div>
      <h1>{trigger.phrase}</h1>
      <p>Score: {trigger.trigger_score}</p>
      <SourceEvidencePanel
        brandId={brandId}
        sourcePageIds={trigger.source_page_ids ?? []}
        promptRunIds={trigger.prompt_run_ids ?? []}
      />
      <div className="filters">
        <button type="button" onClick={() => decide("approve")}>
          Approve
        </button>
        <button type="button" onClick={() => decide("reject")}>
          Reject
        </button>
        <button type="button" onClick={() => decide("too_broad")}>
          Too broad
        </button>
        <button type="button" onClick={() => decide("mark_for_testing")}>
          Mark for testing
        </button>
      </div>
    </div>
  );
}
