const styles = {
  pending: "bg-slate-100 text-slate-700",
  queued: "bg-amber-100 text-amber-800",
  planning: "bg-blue-100 text-blue-800",
  searching: "bg-cyan-100 text-cyan-800",
  evaluating: "bg-indigo-100 text-indigo-800",
  summarizing: "bg-violet-100 text-violet-800",
  analyzing: "bg-purple-100 text-purple-800",
  critiquing: "bg-fuchsia-100 text-fuchsia-800",
  writing: "bg-pink-100 text-pink-800",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  high: "bg-emerald-100 text-emerald-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-red-100 text-red-800",
  unknown: "bg-slate-100 text-slate-600",
};

export default function Badge({ children, status, variant, className = "" }) {
  const key = (variant || status || "pending").toLowerCase();
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium capitalize ${styles[key] || styles.pending} ${className}`}
    >
      {children || status || variant}
    </span>
  );
}
