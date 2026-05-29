import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export function BrandSetupPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [competitors, setCompetitors] = useState("");
  const [topics, setTopics] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.createBrand({
        name: name.trim(),
        primary_domain: domain.trim(),
        competitor_domains: competitors
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        seed_topics: topics
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        run_ingestion: true,
      });
      navigate(`/brands/${res.brand_id}/runs`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      <h1>New brand</h1>
      <form className="card form-card" onSubmit={onSubmit}>
        <label>
          Brand name
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme Analytics"
          />
        </label>
        <label>
          Primary domain
          <input
            required
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="acme.com"
          />
        </label>
        <label>
          Competitor domains (comma-separated)
          <input
            value={competitors}
            onChange={(e) => setCompetitors(e.target.value)}
            placeholder="rival.com, other.com"
          />
        </label>
        <label>
          Seed topics (comma-separated)
          <input
            value={topics}
            onChange={(e) => setTopics(e.target.value)}
            placeholder="product analytics, funnels"
          />
        </label>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button type="submit" disabled={submitting}>
          {submitting ? "Starting ingestion…" : "Create & ingest"}
        </button>
      </form>
    </div>
  );
}
