export default function CredibilityBadge({ score, tier }) {
  const resolvedTier =
    tier ||
    (score == null ? "unknown" : score >= 8 ? "high" : score >= 5 ? "medium" : "low");

  const styles = {
    high: "bg-emerald-100 text-emerald-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-red-100 text-red-800",
    unknown: "bg-slate-100 text-slate-600",
  };

  const labels = {
    high: "High",
    medium: "Medium",
    low: "Low",
    unknown: "N/A",
  };

  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${styles[resolvedTier]}`}
    >
      {labels[resolvedTier]}
      {score != null ? ` (${score}/10)` : ""}
    </span>
  );
}
