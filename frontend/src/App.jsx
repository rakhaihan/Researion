import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import HistoryPage from "./pages/HistoryPage";
import HomePage from "./pages/HomePage";
import NewResearchPage from "./pages/NewResearchPage";
import ResearchDetailPage from "./pages/ResearchDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="new" element={<NewResearchPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="research/:id" element={<ResearchDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
