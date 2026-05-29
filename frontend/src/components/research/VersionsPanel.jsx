import { useEffect, useState } from "react";
import Button from "../ui/Button";
import Alert from "../ui/Alert";
import { api } from "../../services/api";

export default function VersionsPanel({ researchId, onRestored }) {
  const [versions, setVersions] = useState([]);
  const [compareFrom, setCompareFrom] = useState("");
  const [compareTo, setCompareTo] = useState("");
  const [diff, setDiff] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!researchId) return;
    api.listVersions(researchId).then(setVersions).catch(() => setVersions([]));
  }, [researchId]);

  async function handleCompare() {
    if (!compareFrom || !compareTo) return;
    try {
      const result = await api.compareVersions(
        researchId,
        Number(compareFrom),
        Number(compareTo),
      );
      setDiff(result);
    } catch (err) {
      setError(err.message || "Compare failed");
    }
  }

  async function handleRestore(versionId) {
    try {
      await api.restoreVersion(researchId, versionId);
      onRestored?.();
      const updated = await api.listVersions(researchId);
      setVersions(updated);
    } catch (err) {
      setError(err.message || "Restore failed");
    }
  }

  if (!versions.length) {
    return <p className="text-sm text-slate-500">No saved versions yet.</p>;
  }

  return (
    <div className="space-y-4">
      {error && <Alert variant="error">{error}</Alert>}
      <ul className="space-y-2">
        {versions.map((v) => (
          <li
            key={v.id}
            className="flex flex-col gap-2 rounded-xl border border-slate-200 p-3 text-sm sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-semibold text-slate-900">Version {v.version_number}</p>
              <p className="text-xs text-slate-500">
                {new Date(v.created_at).toLocaleString()}
                {v.change_reason ? ` · ${v.change_reason}` : ""}
              </p>
              {v.quality_score != null && (
                <p className="text-xs text-slate-600">Quality: {v.quality_score.toFixed(1)}</p>
              )}
            </div>
            <Button variant="secondary" size="sm" onClick={() => handleRestore(v.id)}>
              Restore
            </Button>
          </li>
        ))}
      </ul>
      <div className="rounded-xl border border-slate-200 p-4">
        <p className="mb-2 text-sm font-medium text-slate-800">Compare versions</p>
        <div className="flex flex-wrap gap-2">
          <select
            value={compareFrom}
            onChange={(e) => setCompareFrom(e.target.value)}
            className="rounded-lg border border-slate-200 px-2 py-1 text-sm"
          >
            <option value="">From</option>
            {versions.map((v) => (
              <option key={v.id} value={v.version_number}>
                v{v.version_number}
              </option>
            ))}
          </select>
          <select
            value={compareTo}
            onChange={(e) => setCompareTo(e.target.value)}
            className="rounded-lg border border-slate-200 px-2 py-1 text-sm"
          >
            <option value="">To</option>
            {versions.map((v) => (
              <option key={v.id} value={v.version_number}>
                v{v.version_number}
              </option>
            ))}
          </select>
          <Button variant="secondary" size="sm" onClick={handleCompare}>
            Compare
          </Button>
        </div>
        {diff && (
          <div className="mt-3 space-y-2 text-xs text-slate-600">
            <p>{diff.changed_summary}</p>
            <pre className="max-h-48 overflow-auto rounded-lg bg-slate-900 p-3 text-slate-100">
              {diff.markdown_diff || "No diff"}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
