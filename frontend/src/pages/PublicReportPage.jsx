import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Alert from "../components/ui/Alert";
import ReportViewer from "../components/research/ReportViewer";
import SourcesPanel from "../components/research/SourcesPanel";
import { api, getPublicApiBase } from "../services/api";

export default function PublicReportPage() {
  const { token } = useParams();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getPublicReport(token)
      .then(setReport)
      .catch((err) => setError(err.message || "Report not found"));
  }, [token]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <Alert variant="error">{error}</Alert>
      </div>
    );
  }

  if (!report) {
    return <p className="p-8 text-center text-slate-500">Loading shared report…</p>;
  }

  const sources = (report.sources || []).map((s, i) => ({
    id: String(i),
    citation_key: s.citation_key,
    title: s.title,
    url: s.source_type === "document" ? `document://shared` : "#",
    snippet: s.snippet || "",
    source_type: s.source_type,
    page_number: s.page_number,
  }));

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">Shared report</p>
        <h1 className="text-2xl font-bold text-slate-900">{report.title}</h1>
        <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
          {report.quality_status && <Badge status={report.quality_status}>{report.quality_status}</Badge>}
          {report.quality_score != null && <span>Score: {report.quality_score.toFixed(1)}</span>}
          <span>Updated {new Date(report.updated_at).toLocaleString()}</span>
        </div>
        {report.allow_download && (
          <div className="mt-3 flex gap-2">
            <a
              href={`${getPublicApiBase()}/public/reports/${token}/export/markdown`}
              className="text-sm text-brand-600 hover:underline"
            >
              Download Markdown
            </a>
            <a
              href={`${getPublicApiBase()}/public/reports/${token}/export/pdf`}
              className="text-sm text-brand-600 hover:underline"
            >
              Download PDF
            </a>
          </div>
        )}
      </header>
      <main className="mx-auto max-w-4xl space-y-6 p-6">
        <Card>
          <ReportViewer researchId={null} markdownContent={report.markdown_content} />
        </Card>
        <Card>
          <SourcesPanel sources={sources} />
        </Card>
      </main>
    </div>
  );
}
