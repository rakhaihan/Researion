import { useEffect, useState } from "react";
import Button from "../ui/Button";
import Alert from "../ui/Alert";
import { api } from "../../services/api";

export default function ShareModal({ researchId, open, onClose }) {
  const [links, setLinks] = useState([]);
  const [visibility, setVisibility] = useState("public");
  const [allowDownload, setAllowDownload] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !researchId) return;
    api.listShareLinks(researchId).then(setLinks).catch(() => setLinks([]));
  }, [open, researchId]);

  async function handleCreate() {
    setLoading(true);
    setError("");
    try {
      const link = await api.createShareLink(researchId, {
        visibility,
        allow_download: allowDownload,
      });
      setLinks((prev) => [link, ...prev]);
    } catch (err) {
      setError(err.message || "Failed to create share link");
    } finally {
      setLoading(false);
    }
  }

  async function handleRevoke(shareId) {
    await api.revokeShareLink(researchId, shareId);
    setLinks((prev) => prev.filter((l) => l.id !== shareId));
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-900">Share report</h3>
          <button type="button" onClick={onClose} className="text-slate-500 hover:text-slate-800">
            ✕
          </button>
        </div>
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-3">
          <label className="block text-sm">
            <span className="font-medium text-slate-700">Visibility</span>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            >
              <option value="public">Public (anyone with link)</option>
              <option value="private">Private link</option>
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={allowDownload}
              onChange={(e) => setAllowDownload(e.target.checked)}
            />
            Allow download (Markdown/PDF)
          </label>
          <Button onClick={handleCreate} disabled={loading} className="w-full">
            {loading ? "Creating…" : "Create share link"}
          </Button>
        </div>
        <ul className="mt-6 space-y-3">
          {links.map((link) => (
            <li key={link.id} className="rounded-xl border border-slate-200 p-3 text-sm">
              <p className="break-all font-mono text-xs text-brand-700">{link.share_url}</p>
              <p className="mt-1 text-xs text-slate-500">
                {link.visibility} · download {link.allow_download ? "on" : "off"}
                {link.revoked_at ? " · revoked" : ""}
              </p>
              <div className="mt-2 flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => navigator.clipboard.writeText(link.share_url)}
                >
                  Copy link
                </Button>
                {!link.revoked_at && (
                  <Button variant="ghost" size="sm" onClick={() => handleRevoke(link.id)}>
                    Revoke
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
