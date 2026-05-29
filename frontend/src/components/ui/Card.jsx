export default function Card({ children, className = "", padding = true, ...props }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white shadow-card ${padding ? "p-6" : ""} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}
