import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import PageHeader from "../components/ui/PageHeader";
import { SkeletonList } from "../components/ui/Skeleton";
import Badge from "../components/ui/Badge";
import Alert from "../components/ui/Alert";
import { api } from "../services/api";
import { RUNNING_STATUSES } from "../utils/researchConfig";

const PIPELINE = [
  "Planner",
  "Search",
  "Evaluator",
  "Summarizer",
  "Analyst",
  "Critique",
  "Report Writer",
];

export default function HomePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await api.listResearch();
        setItems(data);
      } catch (err) {
        setError(err.message || "Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = useMemo(() => {
    const total = items.length;
    const completed = items.filter((i) => i.status === "completed").length;
    const running = items.filter((i) => RUNNING_STATUSES.has(i.status)).length;
    const failed = items.filter((i) => i.status === "failed").length;
    return { total, completed, running, failed };
  }, [items]);

  const recent = useMemo(
    () =>
      [...items]
        .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        .slice(0, 5),
    [items],
  );

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-brand-600 to-indigo-700 p-8 text-white shadow-card">
        <p className="mb-2 text-sm font-medium text-brand-100">
          AI-powered multi-agent research workspace
        </p>
        <h2 className="mb-4 text-3xl font-bold tracking-tight">
          Automate deep research with specialized agents
        </h2>
        <p className="mb-6 max-w-2xl text-brand-100">
          Researion orchestrates planning, live search, credibility evaluation, summarization,
          analysis, critique, and citation-aware report writing in one workflow.
        </p>
        <Link to="/new">
          <Button className="bg-white text-brand-700 hover:bg-brand-50">New Research</Button>
        </Link>
      </section>

      {error && <Alert variant="error">{error}</Alert>}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Total research", value: stats.total },
          { label: "Completed", value: stats.completed },
          { label: "Running", value: stats.running },
          { label: "Failed", value: stats.failed },
        ].map((stat) => (
          <Card key={stat.label} className="text-center">
            <p className="text-3xl font-bold text-slate-900">{loading ? "—" : stat.value}</p>
            <p className="mt-1 text-sm text-slate-600">{stat.label}</p>
          </Card>
        ))}
      </section>

      <section>
        <PageHeader
          title="Recent research"
          description="Pick up where you left off or open completed reports."
        />
        {loading ? (
          <SkeletonList count={3} />
        ) : recent.length === 0 ? (
          <Card>
            <p className="text-sm text-slate-600">No projects yet. Start your first research run.</p>
          </Card>
        ) : (
          <div className="space-y-3">
            {recent.map((item) => (
              <Card key={item.id} className="hover:border-brand-200">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="mb-2 flex flex-wrap gap-2">
                      <Badge status={item.status} />
                      <span className="text-xs text-slate-500">{item.research_type}</span>
                    </div>
                    <h3 className="font-semibold text-slate-900">{item.topic}</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      Updated {new Date(item.updated_at).toLocaleString()}
                    </p>
                  </div>
                  <Link to={`/research/${item.id}`}>
                    <Button variant="secondary" size="sm">
                      Open
                    </Button>
                  </Link>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <PageHeader title="Agent pipeline" description="How Researion processes your topic end-to-end." />
        <Card>
          <div className="flex flex-wrap gap-2">
            {PIPELINE.map((agent, index) => (
              <span key={agent} className="flex items-center gap-2 text-sm text-slate-700">
                <span className="rounded-lg bg-brand-50 px-3 py-1.5 font-medium text-brand-800">
                  {agent}
                </span>
                {index < PIPELINE.length - 1 && <span className="text-slate-300">→</span>}
              </span>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
