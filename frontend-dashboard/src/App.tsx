import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { BrandListPage } from "./pages/BrandListPage";
import { BrandSetupPage } from "./pages/BrandSetupPage";
import { BrandOverviewPage } from "./pages/BrandOverviewPage";
import { RunStatusPage } from "./pages/RunStatusPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { TriggerRankingPage } from "./pages/TriggerRankingPage";
import { TriggerDetailPage } from "./pages/TriggerDetailPage";
import { ExportPage } from "./pages/ExportPage";

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<BrandListPage />} />
        <Route path="/brands/new" element={<BrandSetupPage />} />
        <Route path="/brands/:brandId" element={<BrandOverviewPage />} />
        <Route path="/brands/:brandId/runs" element={<RunStatusPage />} />
        <Route path="/brands/:brandId/knowledge" element={<KnowledgePage />} />
        <Route path="/brands/:brandId/triggers" element={<TriggerRankingPage />} />
        <Route
          path="/brands/:brandId/triggers/:triggerId"
          element={<TriggerDetailPage />}
        />
        <Route path="/brands/:brandId/export" element={<ExportPage />} />
      </Routes>
    </AppLayout>
  );
}
