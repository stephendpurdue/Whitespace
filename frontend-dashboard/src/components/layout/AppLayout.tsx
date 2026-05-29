import { NavLink, useParams } from "react-router-dom";
import type { ReactNode } from "react";

export function AppLayout({ children }: { children: ReactNode }) {
  const { brandId } = useParams();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>Trigger Discovery</h2>
        <nav>
          <NavLink to="/" end>
            Projects
          </NavLink>
          <NavLink to="/brands/new">New brand</NavLink>
          {brandId && (
            <>
              <hr />
              <NavLink to={`/brands/${brandId}`} end>
                Overview
              </NavLink>
              <NavLink to={`/brands/${brandId}/runs`}>Runs</NavLink>
              <NavLink to={`/brands/${brandId}/knowledge`}>Knowledge</NavLink>
              <NavLink to={`/brands/${brandId}/triggers`}>Triggers</NavLink>
              <NavLink to={`/brands/${brandId}/export`}>Export</NavLink>
            </>
          )}
        </nav>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}
