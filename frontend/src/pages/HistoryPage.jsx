import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import PageHeader from "../components/ui/PageHeader";
import EmptyState from "../components/ui/EmptyState";
import Alert from "../components/ui/Alert";
import { SkeletonList } from "../components/ui/Skeleton";
import { api } from "../services/api";
import { RESEARCH_TYPES } from "../utils/researchConfig";

const STATUS_OPTIONS = [
  "",
  "pending",
  "queued",
  "planning",
  "searching",
  "evaluating",
  "summarizing",
  "analyzing",
  "critiquing",
  "writing",
  "completed",
  "failed",
];

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    async function loadHistory() {
      try {
        const data = await api.listResearch();
        setItems(data);
      } catch (err) {
        setError(err.message || "Failed to load research history");
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  const filtered = useMemo(() => {
    return [...items]
      .filter((item) => {
        if (query && !item.topic.toLowerCase().includes(query.toLowerCase())) return false;
        if (typeFilter && item.research_type !== typeFilter) return false;
        if (statusFilter && item.status !== statusFilter) return false;
        return true;
      })
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
  }, [items, query, typeFilter, statusFilter]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Research history"
        description="Search and filter past projects. Sorted by most recently updated."
      />

      <Card>
        <div className="grid gap-4 md:grid-cols-3">
          <Input
            label="Search topic"
            name="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter by keywords…"
          />
          <Select
            label="Research type"
            name="type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">All types</option>
            {RESEARCH_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>
          <Select
            label="Status"
            name="status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.filter(Boolean).map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <SkeletonList count={4} />
      ) : filtered.length === 0 ? (
        <EmptyState
          title={items.length === 0 ? "No research yet" : "No matches"}
          description={
            items.length === 0
              ? "Create your first project to see it listed here."
              : "Try adjusting filters or search terms."
          }
          actionLabel={items.length === 0 ? "New Research" : undefined}
          onAction={items.length === 0 ? () => (window.location.href = "/new") : undefined}
        />
      ) : (
        <div className="space-y-4">
          {filtered.map((item) => (
            <Card key={item.id} className="hover:border-brand-200">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge status={item.status} />
                    <span className="text-xs text-slate-500">{item.research_type}</span>
                    <span className="text-xs capitalize text-slate-500">Depth: {item.depth}</span>
                  </div>
                  <h3 className="font-semibold text-slate-900">{item.topic}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Created {new Date(item.created_at).toLocaleString()} · Updated{" "}
                    {new Date(item.updated_at).toLocaleString()}
                  </p>
                </div>
                <Link
                  to={`/research/${item.id}`}
                  className="text-sm font-medium text-brand-600 hover:text-brand-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
                >
                  View details →
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
