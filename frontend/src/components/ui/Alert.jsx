const variants = {
  error: "border-red-200 bg-red-50 text-red-800",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  info: "border-blue-200 bg-blue-50 text-blue-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
};

export default function Alert({ children, variant = "info", title, className = "" }) {
  return (
    <div
      className={`rounded-xl border px-4 py-3 text-sm ${variants[variant]} ${className}`}
      role="alert"
    >
      {title && <p className="mb-1 font-semibold">{title}</p>}
      <div>{children}</div>
    </div>
  );
}
