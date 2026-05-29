import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { TriggerCandidate } from "../types/contracts";

export function ExportPage() {
  const { brandId = "" } = useParams();
  const [shortlist, setShortlist] = useState<TriggerCandidate[]>([]);

  useEffect(() => {
    const raw = localStorage.getItem(`decisions:${brandId}`);
    const decisions = raw ? JSON.parse(raw) : [];
    const approved = new Set(
      decisions
        .filter((d: { decision: string }) =>
          ["approve", "mark_for_testing"].includes(d.decision)
        )
        .map((d: { trigger_candidate_id: string }) => d.trigger_candidate_id)
    );
    api.getTriggers(brandId).then((exp) =>
      setShortlist(exp.triggers.filter((t) => approved.has(t.trigger_candidate_id)))
    );
  }, [brandId]);

  const download = () => {
    const blob = new Blob([JSON.stringify(shortlist, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `triggers-${brandId}.json`;
    a.click();
  };

  return (
    <div>
      <h1>Export</h1>
      <p>{shortlist.length} triggers shortlisted for campaign testing.</p>
      <button type="button" onClick={download}>
        Download JSON
      </button>
    </div>
  );
}
