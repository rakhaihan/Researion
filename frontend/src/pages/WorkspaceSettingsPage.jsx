import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Alert from "../components/ui/Alert";
import { api } from "../services/api";

export default function WorkspaceSettingsPage() {
  const { id } = useParams();
  const [workspace, setWorkspace] = useState(null);
  const [members, setMembers] = useState([]);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const [error, setError] = useState("");

  async function load() {
    const [ws, mems] = await Promise.all([
      api.getWorkspace(id),
      api.listWorkspaceMembers(id),
    ]);
    setWorkspace(ws);
    setMembers(mems);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, [id]);

  async function handleInvite(event) {
    event.preventDefault();
    try {
      await api.addWorkspaceMember(id, { email: inviteEmail, role: inviteRole });
      setInviteEmail("");
      await load();
    } catch (err) {
      setError(err.message || "Invite failed");
    }
  }

  async function handleRemove(memberId) {
    await api.removeWorkspaceMember(id, memberId);
    await load();
  }

  if (!workspace) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <Link to="/workspaces" className="text-sm text-brand-600 hover:underline">
        ← Workspaces
      </Link>
      <h2 className="text-2xl font-bold">{workspace.name} — Settings</h2>
      {error && <Alert variant="error">{error}</Alert>}
      <Card>
        <h3 className="mb-3 font-semibold">Members</h3>
        <ul className="mb-4 space-y-2 text-sm">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-2">
              <span>
                {m.full_name} ({m.email}) — {m.role}
              </span>
              {m.role !== "owner" && (
                <Button variant="ghost" size="sm" onClick={() => handleRemove(m.id)}>
                  Remove
                </Button>
              )}
            </li>
          ))}
        </ul>
        <form onSubmit={handleInvite} className="flex flex-col gap-3 sm:flex-row">
          <Input
            label="Invite by email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <Select label="Role" value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
            <option value="admin">Admin</option>
          </Select>
          <Button type="submit" className="self-end">
            Invite
          </Button>
        </form>
      </Card>
    </div>
  );
}
