export default function Select({ label, error, hint, id, className = "", children, ...props }) {
  const selectId = id || props.name;
  const baseClass =
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20";
  const errorClass = error ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : "";

  return (
    <div className={className}>
      {label && (
        <label htmlFor={selectId} className="mb-2 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <select id={selectId} className={`${baseClass} ${errorClass}`} {...props}>
        {children}
      </select>
      {hint && !error && <p className="mt-1.5 text-xs text-slate-500">{hint}</p>}
      {error && <p className="mt-1.5 text-xs text-red-600" role="alert">{error}</p>}
    </div>
  );
}
