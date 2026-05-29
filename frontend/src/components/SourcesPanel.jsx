import CredibilityBadge from "./CredibilityBadge";

function extractDomain(url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return host.startsWith("www.") ? host.slice(4) : host;
  } catch {
    return "";
  }
}

export default function SourcesPanel({ sources, showWarning }) {
  if (!sources?.length) {
    return <p className="text-sm text-slate-500">No sources collected yet.</p>;
  }

  const sorted = [...sources].sort((a, b) => {
    const aNum = parseInt((a.citation_key || "S0").slice(1), 10);
    const bNum = parseInt((b.citation_key || "S0").slice(1), 10);
    return aNum - bNum;
  });

  return (
    <div className="space-y-4">
      {showWarning && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Some sources have low credibility scores. Review citations carefully before acting on
          conclusions.
        </div>
      )}

      <div className="space-y-3">
        {sorted.map((source) => (
          <div
            key={source.id}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="mb-2 flex flex-wrap items-center gap-2">
              {source.citation_key && (
                <span className="rounded-md bg-brand-100 px-2 py-0.5 text-xs font-bold text-brand-700">
                  {source.citation_key}
                </span>
              )}
              <CredibilityBadge
                score={source.credibility_score}
                tier={source.credibility_tier}
              />
              <span className="text-xs text-slate-500">{extractDomain(source.url)}</span>
            </div>

            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="font-medium text-brand-600 hover:underline"
            >
              {source.title}
            </a>

            <p className="mt-2 text-sm text-slate-600 line-clamp-3">{source.snippet}</p>

            {source.credibility_reason && (
              <p className="mt-2 text-xs text-slate-500">
                <span className="font-medium">Credibility:</span> {source.credibility_reason}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
