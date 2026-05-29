import { useWorkspace } from "../../contexts/WorkspaceContext";

export default function WorkspaceSelector() {
  const { workspaces, activeWorkspaceId, setActiveWorkspaceId, loading } = useWorkspace();

  if (loading) {
    return <p className="px-4 text-xs text-slate-500">Loading workspaces…</p>;
  }

  return (
    <div className="border-b border-slate-200 px-4 py-3">
      <label htmlFor="workspace-select" className="mb-1 block text-xs font-medium text-slate-600">
        Workspace
      </label>
      <select
        id="workspace-select"
        value={activeWorkspaceId}
        onChange={(e) => setActiveWorkspaceId(e.target.value)}
        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
      >
        {workspaces.map((ws) => (
          <option key={ws.id} value={ws.id}>
            {ws.name}
            {ws.is_default ? " (default)" : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
