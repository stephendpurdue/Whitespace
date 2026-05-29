export function CrawlSummaryCard({
  pages,
  facts,
}: {
  pages: number;
  facts: number;
}) {
  return (
    <div className="card">
      <h3>Crawl summary</h3>
      <p>Source pages: {pages}</p>
      <p>Normalized facts: {facts}</p>
    </div>
  );
}
