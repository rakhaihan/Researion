import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./contexts/AuthContext";
import { WorkspaceProvider } from "./contexts/WorkspaceContext";
import HistoryPage from "./pages/HistoryPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import NewResearchPage from "./pages/NewResearchPage";
import RegisterPage from "./pages/RegisterPage";
import ResearchDetailPage from "./pages/ResearchDetailPage";
import DocumentsPage from "./pages/DocumentsPage";
import DocumentDetailPage from "./pages/DocumentDetailPage";
import WorkspacesPage from "./pages/WorkspacesPage";
import WorkspaceSettingsPage from "./pages/WorkspaceSettingsPage";
import PublicReportPage from "./pages/PublicReportPage";
import SharedReportsPage from "./pages/SharedReportsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/public/reports/:token" element={<PublicReportPage />} />

          <Route element={<ProtectedRoute />}>
            <Route
              element={
                <WorkspaceProvider>
                  <AppShell />
                </WorkspaceProvider>
              }
            >
              <Route index element={<HomePage />} />
              <Route path="new" element={<NewResearchPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="documents/:id" element={<DocumentDetailPage />} />
              <Route path="workspaces" element={<WorkspacesPage />} />
              <Route path="workspaces/:id/settings" element={<WorkspaceSettingsPage />} />
              <Route path="shared" element={<SharedReportsPage />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="research/:id" element={<ResearchDetailPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
