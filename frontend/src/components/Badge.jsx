const colors = {
  pending: "bg-slate-100 text-slate-700",
  queued: "bg-amber-100 text-amber-700",
  planning: "bg-blue-100 text-blue-700",
  searching: "bg-cyan-100 text-cyan-700",
  evaluating: "bg-indigo-100 text-indigo-700",
  summarizing: "bg-violet-100 text-violet-700",
  analyzing: "bg-purple-100 text-purple-700",
  critiquing: "bg-fuchsia-100 text-fuchsia-700",
  writing: "bg-pink-100 text-pink-700",
  completed: "bg-emerald-100 text-emerald-700",
  failed: "bg-red-100 text-red-700",
};

export default function Badge({ status }) {
  const key = (status || "pending").toLowerCase();
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${colors[key] || colors.pending}`}
    >
      {status}
    </span>
  );
}
