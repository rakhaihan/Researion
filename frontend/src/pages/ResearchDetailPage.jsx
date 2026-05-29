import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Alert from "../components/ui/Alert";
import ProgressBar from "../components/ui/ProgressBar";
import SectionHeader from "../components/ui/SectionHeader";
import { SkeletonList } from "../components/ui/Skeleton";
import WorkflowStepper from "../components/workflow/WorkflowStepper";
import ReportViewer from "../components/research/ReportViewer";
import SourcesPanel from "../components/research/SourcesPanel";
import { useResearchProgress } from "../hooks/useResearchProgress";
import { api } from "../services/api";
import { getStageDescription } from "../utils/workflowSteps";
import { RUNNING_STATUSES } from "../utils/researchConfig";

export default function ResearchDetailPage() {
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [highlightCitation, setHighlightCitation] = useState(null);
  const [debugOpen, setDebugOpen] = useState(false);

  const { progress, transport, startPolling, fetchProgress, isActive } = useResearchProgress(
    id,
    project?.status,
  );

  const loadProject = useCallback(async () => {
    setError("");
    try {
      const data = await api.getResearch(id);
      setProject(data);

      if (data.final_report) {
        setReport(data.final_report);
      } else if (data.status === "completed") {
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
    RUNNING_STATUSES.has(project?.status) ||
    progress?.status === "running" ||
    progress?.status === "queued";

  const canRun = project && project.status !== "completed" && !isRunning;
  const stageDescription = getStageDescription(progress, project?.status);
  const markdownContent = report?.markdown_content || "";
  const failed = progress?.status === "failed" || project?.status === "failed";

  if (loading) {
    return <SkeletonList count={3} />;
  }

  if (!project) {
    return (
      <Card>
        <Alert variant="error" title="Not found">
          Research project could not be loaded.
        </Alert>
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
            <span className="text-xs capitalize text-slate-500">Depth: {project.depth}</span>
            {project.has_report && (
              <span className="text-xs text-emerald-600">Report ready</span>
            )}
          </div>
          <h2 className="text-2xl font-bold text-slate-900">{project.topic}</h2>
          <p className="mt-1 text-sm text-slate-500">
            Created {new Date(project.created_at).toLocaleString()} · Updated{" "}
            {new Date(project.updated_at).toLocaleString()}
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          {canRun && (
            <Button onClick={handleRun} disabled={submitting}>
              {submitting ? "Starting workflow…" : "Run multi-agent workflow"}
            </Button>
          )}
        </div>
      </div>

      {(isRunning || progress) && (
        <Card>
          <SectionHeader
            title="Workflow progress"
            description={stageDescription}
            actions={
              transport !== "idle" && (
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
                  {transport === "sse" ? "Live (SSE)" : "Polling"}
                </span>
              )
            }
          />
          <div className="space-y-6">
            <ProgressBar
              value={progress?.progress_percentage ?? 0}
              label={progress?.current_step_label || stageDescription}
            />
            <WorkflowStepper progress={progress} projectStatus={project.status} />

            <details
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600"
              open={debugOpen}
              onToggle={(e) => setDebugOpen(e.target.open)}
            >
              <summary className="cursor-pointer font-medium text-slate-700">Debug info</summary>
              <dl className="mt-2 space-y-1">
                {progress?.job_id && (
                  <div>
                    <dt className="inline font-medium">job_id: </dt>
                    <dd className="inline font-mono">{progress.job_id}</dd>
                  </div>
                )}
                {progress?.started_at && (
                  <div>
                    <dt className="inline font-medium">started_at: </dt>
                    <dd className="inline">{new Date(progress.started_at).toLocaleString()}</dd>
                  </div>
                )}
                {progress?.updated_at && (
                  <div>
                    <dt className="inline font-medium">updated_at: </dt>
                    <dd className="inline">{new Date(progress.updated_at).toLocaleString()}</dd>
                  </div>
                )}
              </dl>
            </details>
          </div>
        </Card>
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {failed && (project.error_message || progress?.error_message) && (
        <Alert variant="error" title="Workflow failed">
          {progress?.error_message || project.error_message}
        </Alert>
      )}

      <Card>
        <SectionHeader title="Generated questions" />
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

      {markdownContent && (
        <ReportViewer
          researchId={id}
          markdownContent={markdownContent}
          onCitationClick={(key) => {
            setHighlightCitation(key);
            document.getElementById(`source-${key}`)?.scrollIntoView({ behavior: "smooth" });
          }}
        />
      )}

      <Card>
        <SectionHeader
          title="Sources & citations"
          description={
            project.source_count
              ? `${project.source_count} source(s) collected`
              : "Sources appear after search and evaluation"
          }
        />
        <SourcesPanel
          sources={project.sources}
          showWarning={project.low_credibility_warning}
          highlightKey={highlightCitation}
          onHighlight={setHighlightCitation}
        />
      </Card>
    </div>
  );
}
