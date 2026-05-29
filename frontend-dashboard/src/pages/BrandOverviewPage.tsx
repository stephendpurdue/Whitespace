import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { CrawlSummaryCard } from "../components/ui/CrawlSummaryCard";
import type { Brand } from "../types/contracts";

export function BrandOverviewPage() {
  const { brandId = "" } = useParams();
  const [brand, setBrand] = useState<Brand | null>(null);
  const [pages, setPages] = useState(0);
  const [facts, setFacts] = useState(0);
  const [triggers, setTriggers] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getBrand(brandId).then(setBrand).catch(() => setBrand(null));
    Promise.all([
      api.getSourcePages(brandId),
      api.getFacts(brandId),
      api.getTriggers(brandId),
    ])
      .then(([p, f, t]) => {
        setPages(p.length);
        setFacts(f.length);
        setTriggers(t.triggers.length);
        setError(null);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : String(err))
      );
  }, [brandId]);

  return (
    <div>
      <h1>{brand?.name ?? "Brand overview"}</h1>
      {brand && <p className="muted">{brand.primary_domain}</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <CrawlSummaryCard pages={pages} facts={facts} />
      <p>{triggers} ranked triggers</p>
      <nav className="inline-nav">
        <Link to={`/brands/${brandId}/runs`}>Runs</Link>
        <Link to={`/brands/${brandId}/knowledge`}>Knowledge</Link>
        <Link to={`/brands/${brandId}/triggers`}>Triggers</Link>
      </nav>
    </div>
  );
}
