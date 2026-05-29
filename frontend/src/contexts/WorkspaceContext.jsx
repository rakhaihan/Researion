import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";

const STORAGE_KEY = "researion_active_workspace_id";

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const [workspaces, setWorkspaces] = useState([]);
  const [activeWorkspaceId, setActiveWorkspaceIdState] = useState(
    () => localStorage.getItem(STORAGE_KEY) || "",
  );
  const [loading, setLoading] = useState(true);

  const loadWorkspaces = useCallback(async () => {
    try {
      const data = await api.listWorkspaces();
      setWorkspaces(data);
      if (!activeWorkspaceId && data.length > 0) {
        const defaultWs = data.find((w) => w.is_default) || data[0];
        setActiveWorkspaceIdState(defaultWs.id);
        localStorage.setItem(STORAGE_KEY, defaultWs.id);
      }
    } catch {
      setWorkspaces([]);
    } finally {
      setLoading(false);
    }
  }, [activeWorkspaceId]);

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  const setActiveWorkspaceId = useCallback((id) => {
    setActiveWorkspaceIdState(id);
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
  }, []);

  const value = useMemo(
    () => ({
      workspaces,
      activeWorkspaceId,
      setActiveWorkspaceId,
      loading,
      refreshWorkspaces: loadWorkspaces,
      activeWorkspace: workspaces.find((w) => w.id === activeWorkspaceId) || null,
    }),
    [workspaces, activeWorkspaceId, setActiveWorkspaceId, loading, loadWorkspaces],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return ctx;
}
