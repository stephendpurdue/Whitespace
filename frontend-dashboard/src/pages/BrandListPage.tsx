import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Brand } from "../types/contracts";

export function BrandListPage() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listBrands().then(setBrands).catch((e) => setError(String(e)));
  }, []);

  return (
    <div>
      <h1>Brand projects</h1>
      {error && <p role="alert">{error}</p>}
      <ul className="brand-list">
        {brands.map((b) => (
          <li key={b.brand_id}>
            <Link to={`/brands/${b.brand_id}`}>{b.name}</Link> — {b.primary_domain}
          </li>
        ))}
      </ul>
      {!brands.length && !error && <p>No brands yet. Create one to start.</p>}
    </div>
  );
}
