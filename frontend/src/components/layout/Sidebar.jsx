import { NavLink } from "react-router-dom";
import WorkspaceSelector from "../workspace/WorkspaceSelector";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/new", label: "New Research" },
  { to: "/history", label: "History" },
  { to: "/documents", label: "Knowledge Base" },
  { to: "/shared", label: "Shared Reports" },
  { to: "/workspaces", label: "Workspace Settings" },
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-slate-900/40 lg:hidden"
          aria-label="Close navigation"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">
            R
          </div>
          <div>
            <p className="text-lg font-bold tracking-tight text-slate-900">Researion</p>
            <p className="text-xs text-slate-500">Research workspace</p>
          </div>
        </div>
        <WorkspaceSelector />
        <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onClose}
              className={({ isActive }) =>
                `block rounded-xl px-4 py-2.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
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
        <div className="border-t border-slate-200 p-4 text-xs text-slate-500">
          Multi-agent research pipeline
        </div>
      </aside>
    </>
  );
}
