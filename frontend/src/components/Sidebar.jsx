import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/new", label: "New Research" },
  { to: "/history", label: "History" },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block">
      <div className="flex h-full flex-col p-6">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white font-bold">
              R
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">Researion</h1>
              <p className="text-xs text-slate-500">Multi-Agent Research</p>
            </div>
          </div>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto rounded-xl bg-slate-50 p-4 text-xs text-slate-500">
          Powered by LangGraph multi-agent workflow with planner, search, evaluator,
          summarizer, analyst, critique, and report writer agents.
        </div>
      </div>
    </aside>
  );
}
