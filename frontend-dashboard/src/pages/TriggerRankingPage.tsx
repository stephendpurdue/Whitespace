import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { TriggerFilters, type TriggerFilterState } from "../components/ui/TriggerFilters";
import { TriggerTable } from "../components/ui/TriggerTable";
import type { TriggerCandidate } from "../types/contracts";

export function TriggerRankingPage() {
  const { brandId = "" } = useParams();
  const [triggers, setTriggers] = useState<TriggerCandidate[]>([]);
  const [filters, setFilters] = useState<TriggerFilterState>({
    intent: "",
    minScore: 0,
    phraseType: "",
  });

  useEffect(() => {
    api.getTriggers(brandId).then((exp) => setTriggers(exp.triggers));
  }, [brandId]);

  const filtered = useMemo(
    () =>
      triggers.filter((t) => {
        if (filters.intent && t.intent_bucket !== filters.intent) return false;
        if (t.trigger_score < filters.minScore) return false;
        if (filters.phraseType && t.phrase_type !== filters.phraseType) return false;
        return true;
      }),
    [triggers, filters]
  );

  return (
    <div>
      <h1>Trigger ranking</h1>
      <TriggerFilters value={filters} onChange={setFilters} />
      <TriggerTable brandId={brandId} triggers={filtered} />
    </div>
  );
}
