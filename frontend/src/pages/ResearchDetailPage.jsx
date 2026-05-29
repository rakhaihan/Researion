import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import Badge from "../components/Badge";
import Button from "../components/Button";
import Card from "../components/Card";
import LoadingSpinner from "../components/LoadingSpinner";
import ProgressBar from "../components/ProgressBar";
import { useResearchProgress } from "../hooks/useResearchProgress";
import { api, getExportUrl } from "../services/api";

const RUNNING_RESEARCH_STATUSES = new Set([
  "queued",
  "planning",
  "searching",
  "evaluating",
  "summarizing",
  "analyzing",
  "critiquing",
  "writing",
]);

export default function ResearchDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const { progress, startPolling, fetchProgress, isActive } = useResearchProgress(
    id,
    project?.status,
  );

  const loadProject = useCallback(async () => {
    setError("");
    try {
      const data = await api.getResearch(id);
      setProject(data);

      if (data.status === "completed") {
        const reportData = await api.getReport(id);
        setReport(reportData);
      } else {
        setReport(null);
      }
    } catch (err) {
      setError(err.message || "Failed to load research project");
    }
  }, [id]);

  useEffect(() => {
    async function init() {
      setLoading(true);
      await loadProject();
      setLoading(false);
    }
    init();
  }, [loadProject]);

  useEffect(() => {
    if (progress?.status === "completed") {
      loadProject();
    }
  }, [progress?.status, loadProject]);

  async function handleRun() {
    setSubmitting(true);
    setError("");
    try {
      await api.runResearch(id);
      startPolling();
      await fetchProgress();
      await loadProject();
    } catch (err) {
      setError(err.message || "Failed to start research workflow");
      await loadProject();
    } finally {
      setSubmitting(false);
    }
  }

  const isRunning =
    submitting ||
    isActive ||
    RUNNING_RESEARCH_STATUSES.has(project?.status) ||
    progress?.status === "running" ||
    progress?.status === "queued";

  const canRun = project && project.status !== "completed" && !isRunning;
  const progressLabel =
    progress?.current_step_label ||
    (project?.status === "queued" ? "Queued for processing" : "Processing research workflow");

  if (loading) {
    return <LoadingSpinner label="Loading research details..." />;
  }

  if (!project) {
    return (
      <Card>
        <p className="text-sm text-slate-600">Research project not found.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge status={project.status} />
            <span className="text-xs text-slate-500">{project.research_type}</span>
            <span className="text-xs text-slate-500 capitalize">Depth: {project.depth}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900">{project.topic}</h2>
          <p className="mt-1 text-sm text-slate-500">
            Updated {new Date(project.updated_at).toLocaleString()}
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          {canRun && (
            <Button onClick={handleRun} disabled={submitting}>
              {submitting ? "Starting workflow..." : "Run Multi-Agent Workflow"}
            </Button>
          )}
          {report && (
            <>
              <a href={getExportUrl(id, "markdown")} target="_blank" rel="noreferrer">
                <Button variant="secondary">Export Markdown</Button>
              </a>
              <a href={getExportUrl(id, "pdf")} target="_blank" rel="noreferrer">
                <Button variant="secondary">Export PDF</Button>
              </a>
            </>
          )}
        </div>
      </div>

      {(isRunning || progress) && (
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">Workflow Progress</h3>
              {progress?.job_id && (
                <span className="text-xs text-slate-500">Job: {progress.job_id.slice(0, 8)}...</span>
              )}
            </div>
            <ProgressBar
              value={progress?.progress_percentage ?? 0}
              label={progressLabel}
            />
            {isRunning && !progress && (
              <LoadingSpinner label="Waiting for worker to pick up the job..." />
            )}
          </div>
        </Card>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {(project.error_message || progress?.error_message) && (
        <Card>
          <h3 className="mb-2 font-semibold text-red-700">Workflow Error</h3>
          <p className="text-sm text-slate-600">
            {progress?.error_message || project.error_message}
          </p>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h3 className="mb-4 font-semibold text-slate-900">Generated Questions</h3>
          {project.questions?.length ? (
            <ol className="space-y-3 text-sm text-slate-700">
              {project.questions.map((question) => (
                <li key={question.id} className="rounded-lg bg-slate-50 p-3">
                  <span className="mr-2 font-medium text-brand-600">#{question.priority}</span>
                  {question.question}
                </li>
              ))}
            </ol>
          ) : (
            <p className="text-sm text-slate-500">Run the workflow to generate research questions.</p>
          )}
        </Card>

        <Card>
          <h3 className="mb-4 font-semibold text-slate-900">Sources</h3>
          {project.sources?.length ? (
            <div className="space-y-3">
              {project.sources.map((source) => (
                <div key={source.id} className="rounded-lg border border-slate-100 p-3">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-brand-600 hover:underline"
                  >
                    {source.title}
                  </a>
                  <p className="mt-1 text-xs text-slate-500 line-clamp-2">{source.snippet}</p>
                  {source.credibility_score != null && (
                    <p className="mt-2 text-xs font-medium text-slate-600">
                      Credibility: {source.credibility_score}/10
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No sources collected yet.</p>
          )}
        </Card>
      </div>

      {report && (
        <Card>
          <h3 className="mb-4 text-xl font-semibold text-slate-900">Final Report</h3>
          <div className="markdown-body prose max-w-none text-slate-700">
            <ReactMarkdown>{report.markdown_content}</ReactMarkdown>
          </div>
        </Card>
      )}
    </div>
  );
}
