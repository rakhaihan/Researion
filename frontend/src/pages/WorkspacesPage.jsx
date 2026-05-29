import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import PageHeader from "../components/ui/PageHeader";
import Alert from "../components/ui/Alert";
import { api } from "../services/api";
import { useWorkspace } from "../contexts/WorkspaceContext";

export default function WorkspacesPage() {
  const { refreshWorkspaces } = useWorkspace();
  const [workspaces, setWorkspaces] = useState([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const data = await api.listWorkspaces();
    setWorkspaces(data);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    try {
      await api.createWorkspace({ name: name.trim() });
      setName("");
      await load();
      await refreshWorkspaces();
    } catch (err) {
      setError(err.message || "Failed to create workspace");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Workspaces" description="Organize research projects by team or topic." />
      {error && <Alert variant="error">{error}</Alert>}
      <Card>
        <form onSubmit={handleCreate} className="flex flex-col gap-3 sm:flex-row">
          <Input
            label="New workspace name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="flex-1"
          />
          <Button type="submit" className="self-end">
            Create workspace
          </Button>
        </form>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        {workspaces.map((ws) => (
          <Card key={ws.id}>
            <h3 className="font-semibold text-slate-900">{ws.name}</h3>
            <p className="text-xs text-slate-500">Role: {ws.role || "member"}</p>
            <div className="mt-3 flex gap-2">
              <Link to={`/workspaces/${ws.id}`}>
                <Button variant="secondary" size="sm">
                  Open
                </Button>
              </Link>
              <Link to={`/workspaces/${ws.id}/settings`}>
                <Button variant="ghost" size="sm">
                  Settings
                </Button>
              </Link>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
