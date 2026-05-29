import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/Badge";
import Card from "../components/Card";
import LoadingSpinner from "../components/LoadingSpinner";
import { api } from "../services/api";

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  if (loading) {
    return <LoadingSpinner label="Loading research history..." />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Research History</h2>
        <p className="text-sm text-slate-600">Browse previous research projects and open details.</p>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <Card>
          <p className="text-sm text-slate-600">No research projects yet.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <Card key={item.id} className="hover:border-brand-200 transition">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <Badge status={item.status} />
                    <span className="text-xs text-slate-500">{item.research_type}</span>
                  </div>
                  <h3 className="font-semibold text-slate-900">{item.topic}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Created {new Date(item.created_at).toLocaleString()}
                  </p>
                </div>
                <Link
                  to={`/research/${item.id}`}
                  className="text-sm font-medium text-brand-600 hover:text-brand-700"
                >
                  View details
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
