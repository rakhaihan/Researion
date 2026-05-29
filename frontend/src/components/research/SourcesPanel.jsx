import { useMemo, useState } from "react";
import Badge from "../ui/Badge";
import Alert from "../ui/Alert";
import EmptyState from "../ui/EmptyState";

const FILTERS = [
  { value: "all", label: "All" },
  { value: "high", label: "High credibility" },
  { value: "medium", label: "Medium credibility" },
  { value: "low", label: "Low credibility" },
];

function extractDomain(url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return host.startsWith("www.") ? host.slice(4) : host;
  } catch {
    return "";
  }
}

function CredibilityBadge({ score, tier }) {
  const resolved = tier || (score == null ? "unknown" : score >= 8 ? "high" : score >= 5 ? "medium" : "low");
  const label = score != null ? `${resolved} (${score.toFixed(1)})` : resolved;
  return <Badge variant={resolved}>{label}</Badge>;
}

export default function SourcesPanel({ sources, showWarning, highlightKey, onHighlight }) {
  const [filter, setFilter] = useState("all");

  const sorted = useMemo(() => {
    if (!sources?.length) return [];
    return [...sources].sort((a, b) => {
      const aNum = parseInt((a.citation_key || "S0").slice(1), 10);
      const bNum = parseInt((b.citation_key || "S0").slice(1), 10);
      return aNum - bNum;
    });
  }, [sources]);

  const filtered = useMemo(() => {
    if (filter === "all") return sorted;
    return sorted.filter((s) => (s.credibility_tier || "unknown") === filter);
  }, [sorted, filter]);

  const lowCount = sorted.filter((s) => s.credibility_tier === "low").length;

  if (!sources?.length) {
    return (
      <EmptyState
        title="No sources yet"
        description="Run the workflow to collect and evaluate web sources with citation keys."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
              filter === f.value
                ? "bg-brand-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {(showWarning || lowCount > 0) && (
        <Alert variant="warning" title="Low credibility sources detected">
          {lowCount} source(s) scored below the medium threshold. Verify claims before relying on
          them.
        </Alert>
      )}

      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No sources match this filter.</p>
      ) : (
        <div className="space-y-3">
          {filtered.map((source) => {
            const highlighted = highlightKey && source.citation_key === highlightKey;
            return (
              <article
                key={source.id}
                id={source.citation_key ? `source-${source.citation_key}` : undefined}
                className={`rounded-xl border p-4 transition ${
                  highlighted
                    ? "border-brand-400 bg-brand-50 ring-2 ring-brand-200"
                    : "border-slate-200 bg-white"
                }`}
              >
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  {source.citation_key && (
                    <button
                      type="button"
                      className="rounded-md bg-brand-100 px-2 py-0.5 text-xs font-bold text-brand-700 hover:bg-brand-200 focus-visible:ring-2 focus-visible:ring-brand-500"
                      onClick={() => onHighlight?.(source.citation_key)}
                    >
                      {source.citation_key}
                    </button>
                  )}
                  <CredibilityBadge score={source.credibility_score} tier={source.credibility_tier} />
                  {source.source_type && (
                    <span className="text-xs text-slate-500">{source.source_type}</span>
                  )}
                  <span className="text-xs text-slate-500">
                    {source.domain || extractDomain(source.url)}
                  </span>
                </div>

                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-brand-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                >
                  {source.title}
                </a>

                {source.snippet && (
                  <p className="mt-2 line-clamp-3 text-sm text-slate-600">{source.snippet}</p>
                )}

                <dl className="mt-3 grid gap-1 text-xs text-slate-500 sm:grid-cols-2">
                  {source.published_date && (
                    <div>
                      <dt className="inline font-medium text-slate-600">Published: </dt>
                      <dd className="inline">{source.published_date}</dd>
                    </div>
                  )}
                  {source.accessed_at && (
                    <div>
                      <dt className="inline font-medium text-slate-600">Accessed: </dt>
                      <dd className="inline">{new Date(source.accessed_at).toLocaleString()}</dd>
                    </div>
                  )}
                </dl>

                {source.credibility_reason && (
                  <details className="mt-2 text-xs text-slate-600">
                    <summary className="cursor-pointer font-medium text-slate-700">
                      Credibility rationale
                    </summary>
                    <p className="mt-1">{source.credibility_reason}</p>
                  </details>
                )}
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
