import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { NormalizedFact } from "../types/contracts";

export function KnowledgePage() {
  const { brandId = "" } = useParams();
  const [facts, setFacts] = useState<NormalizedFact[]>([]);

  useEffect(() => {
    api.getFacts(brandId).then(setFacts);
  }, [brandId]);

  return (
    <div>
      <h1>Brand knowledge</h1>
      <table>
        <thead>
          <tr>
            <th>URL</th>
            <th>Type</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          {facts.map((f) => (
            <tr key={f.normalized_fact_id}>
              <td>{f.url}</td>
              <td>{f.page_type}</td>
              <td>{f.summary ?? f.title}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
