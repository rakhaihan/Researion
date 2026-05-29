export default function Input({
  label,
  error,
  hint,
  id,
  className = "",
  textarea = false,
  rows = 4,
  ...props
}) {
  const inputId = id || props.name;
  const baseClass =
    "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 disabled:bg-slate-50";
  const errorClass = error ? "border-red-300 focus:border-red-500 focus:ring-red-500/20" : "";

  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="mb-2 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      {textarea ? (
        <textarea id={inputId} rows={rows} className={`${baseClass} ${errorClass}`} {...props} />
      ) : (
        <input id={inputId} className={`${baseClass} ${errorClass}`} {...props} />
      )}
      {hint && !error && <p className="mt-1.5 text-xs text-slate-500">{hint}</p>}
      {error && <p className="mt-1.5 text-xs text-red-600" role="alert">{error}</p>}
    </div>
  );
}
