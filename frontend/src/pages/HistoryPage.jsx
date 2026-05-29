import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import PageHeader from "../components/ui/PageHeader";
import EmptyState from "../components/ui/EmptyState";
import Alert from "../components/ui/Alert";
import { SkeletonList } from "../components/ui/Skeleton";
import { api } from "../services/api";
import { useWorkspace } from "../contexts/WorkspaceContext";
import { RESEARCH_TYPES } from "../utils/researchConfig";

const STATUS_OPTIONS = [
  "",
  "pending",
  "completed",
  "failed",
  "planning",
  "searching",
];

const SOURCE_MODES = ["", "web_only", "documents_only", "hybrid"];

export default function HistoryPage() {
  const { activeWorkspaceId } = useWorkspace();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sourceMode, setSourceMode] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [sort, setSort] = useState("latest");

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = { sort };
      if (activeWorkspaceId) params.workspace_id = activeWorkspaceId;
      if (query) params.q = query;
      if (typeFilter) params.research_type = typeFilter;
      if (statusFilter) params.status = statusFilter;
      if (sourceMode) params.source_mode = sourceMode;
      if (showArchived) params.archived = true;
      const data = await api.listResearch(params);
      setItems(data);
    } catch (err) {
      setError(err.message || "Failed to load research history");
    } finally {
      setLoading(false);
    }
  }, [activeWorkspaceId, query, typeFilter, statusFilter, sourceMode, showArchived, sort]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const pinned = useMemo(() => items.filter((i) => i.is_pinned && !i.archived_at), [items]);
  const rest = useMemo(() => items.filter((i) => !i.is_pinned), [items]);

  async function handlePin(item, pin) {
    if (pin) await api.pinResearch(item.id);
    else await api.unpinResearch(item.id);
    await loadHistory();
  }

  async function handleArchive(item, archive) {
    if (archive) await api.archiveResearch(item.id);
    else await api.restoreResearch(item.id);
    await loadHistory();
  }

  function renderItem(item) {
    return (
      <Card key={item.id}>
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-2 flex flex-wrap gap-2">
              <Badge status={item.status} />
              {item.is_pinned && (
                <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-800">
                  Pinned
                </span>
              )}
              {item.archived_at && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  Archived
                </span>
              )}
            </div>
            <Link to={`/research/${item.id}`} className="font-semibold text-brand-700 hover:underline">
              {item.topic}
            </Link>
            <p className="mt-1 text-xs text-slate-500">
              {item.research_type} · {item.research_source_mode} ·{" "}
              {new Date(item.updated_at).toLocaleString()}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePin(item, !item.is_pinned)}
            >
              {item.is_pinned ? "Unpin" : "Pin"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleArchive(item, !item.archived_at)}
            >
              {item.archived_at ? "Restore" : "Archive"}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Research history" description="Filter, pin, and archive projects in your workspace." />
      {error && <Alert variant="error">{error}</Alert>}
      <Card>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Input label="Search topic" value={query} onChange={(e) => setQuery(e.target.value)} />
          <Select label="Type" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">All types</option>
            {RESEARCH_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
          <Select label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All statuses</option>
            {STATUS_OPTIONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </Select>
          <Select label="Source mode" value={sourceMode} onChange={(e) => setSourceMode(e.target.value)}>
            <option value="">All modes</option>
            {SOURCE_MODES.filter(Boolean).map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </Select>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            Show archived
          </label>
          <Select label="Sort" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="latest">Latest</option>
            <option value="oldest">Oldest</option>
            <option value="title">Title</option>
          </Select>
        </div>
      </Card>
      {loading ? (
        <SkeletonList count={4} />
      ) : items.length === 0 ? (
        <EmptyState title="No research yet" description="Create a new research project to get started." />
      ) : (
        <div className="space-y-6">
          {pinned.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold text-slate-700">Pinned</h3>
              <div className="space-y-3">{pinned.map(renderItem)}</div>
            </section>
          )}
          <section>
            {pinned.length > 0 && (
              <h3 className="mb-3 text-sm font-semibold text-slate-700">All research</h3>
            )}
            <div className="space-y-3">{rest.map(renderItem)}</div>
          </section>
        </div>
      )}
    </div>
  );
}
