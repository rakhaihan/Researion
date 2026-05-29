export default function Button({
  children,
  variant = "primary",
  className = "",
  disabled = false,
  ...props
}) {
  const variants = {
    primary:
      "bg-brand-600 hover:bg-brand-700 text-white shadow-sm disabled:bg-brand-300",
    secondary:
      "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 disabled:bg-slate-100",
    danger: "bg-red-600 hover:bg-red-700 text-white disabled:bg-red-300",
  };

  return (
    <button
      className={`inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
