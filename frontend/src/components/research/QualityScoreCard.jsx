import Badge from "../ui/Badge";
import Card from "../ui/Card";
import Alert from "../ui/Alert";
import SectionHeader from "../ui/SectionHeader";

const STATUS_LABELS = {
  passed: { label: "Passed", variant: "completed" },
  warning: { label: "Warning", variant: "queued" },
  failed: { label: "Failed", variant: "failed" },
};

function ScoreBar({ label, value }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-800">{value ?? 0}/100</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100">
        <div
          className="h-2 rounded-full bg-brand-600 transition-all"
          style={{ width: `${Math.min(100, value ?? 0)}%` }}
        />
      </div>
    </div>
  );
}

export default function QualityScoreCard({
  qualityEvaluation,
  qualityStatus,
  qualityScore,
  warnings,
  recommendations,
  onRegenerate,
  regenerating,
}) {
  if (!qualityEvaluation && qualityScore == null) {
    return null;
  }

  const evalData = qualityEvaluation || {};
  const statusKey = (qualityStatus || evalData.quality_status || "warning").toLowerCase();
  const statusMeta = STATUS_LABELS[statusKey] || STATUS_LABELS.warning;
  const overall = qualityScore ?? evalData.overall_score ?? 0;

  const invalidCitations = evalData.citation_validation?.invalid_citations || [];

  return (
    <Card>
      <SectionHeader
        title="Research quality"
        description="Citation validation, source diversity, and report completeness."
        actions={
          onRegenerate && (statusKey === "warning" || statusKey === "failed") ? (
            <button
              type="button"
              onClick={onRegenerate}
              disabled={regenerating}
              className="rounded-lg border border-brand-600 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700 hover:bg-brand-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-50"
            >
              {regenerating ? "Regenerating…" : "Regenerate report"}
            </button>
          ) : null
        }
      />

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-slate-100">
          <span className="text-2xl font-bold text-slate-900">{Math.round(overall)}</span>
        </div>
        <div>
          <Badge status={statusMeta.variant}>{statusMeta.label}</Badge>
          <p className="mt-2 text-sm text-slate-600">Overall quality score (0–100)</p>
        </div>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <ScoreBar label="Citation" value={evalData.citation_score} />
        <ScoreBar label="Source diversity" value={evalData.source_diversity_score} />
        <ScoreBar label="Source credibility" value={evalData.source_credibility_score} />
        <ScoreBar label="Freshness" value={evalData.freshness_score} />
        <ScoreBar label="Completeness" value={evalData.completeness_score} />
      </div>

      {invalidCitations.length > 0 && (
        <Alert variant="error" title="Fictitious citations detected">
          The report references unknown citation keys: {invalidCitations.join(", ")}. These
          citations are not backed by collected sources.
        </Alert>
      )}

      {(warnings?.length > 0 || evalData.warnings?.length > 0) && (
        <Alert variant="warning" title="Quality warnings" className="mt-4">
          <ul className="list-disc space-y-1 pl-5">
            {(warnings || evalData.warnings || []).map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </Alert>
      )}

      {(recommendations?.length > 0 || evalData.recommendations?.length > 0) && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="mb-2 text-sm font-semibold text-slate-800">Recommendations</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
            {(recommendations || evalData.recommendations || []).map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
