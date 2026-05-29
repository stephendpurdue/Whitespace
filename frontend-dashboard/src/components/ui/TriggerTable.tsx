import { Link } from "react-router-dom";
import type { TriggerCandidate } from "../../types/contracts";

export function TriggerTable({
  brandId,
  triggers,
}: {
  brandId: string;
  triggers: TriggerCandidate[];
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Phrase</th>
          <th>Score</th>
          <th>Intent</th>
          <th>Action</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {triggers.map((t) => (
          <tr key={t.trigger_candidate_id}>
            <td>{t.phrase}</td>
            <td>{t.trigger_score.toFixed(2)}</td>
            <td>{t.intent_bucket}</td>
            <td>{t.recommended_action}</td>
            <td>
              <Link to={`/brands/${brandId}/triggers/${t.trigger_candidate_id}`}>
                Details
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
