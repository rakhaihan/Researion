import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/Button";
import Card from "../components/Card";
import LoadingSpinner from "../components/LoadingSpinner";
import { api } from "../services/api";

const RESEARCH_TYPES = [
  "Market Research",
  "Stock/Crypto Research",
  "Academic Research",
  "Competitor Analysis",
  "Technology Trend Analysis",
];

const DEPTH_OPTIONS = [
  { value: "quick", label: "Quick" },
  { value: "standard", label: "Standard" },
  { value: "deep", label: "Deep" },
];

export default function NewResearchPage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState("");
  const [researchType, setResearchType] = useState(RESEARCH_TYPES[1]);
  const [depth, setDepth] = useState("standard");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const project = await api.createResearch({
        topic,
        research_type: researchType,
        depth,
      });
      navigate(`/research/${project.id}`);
    } catch (err) {
      setError(err.message || "Failed to create research project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">New Research</h2>
        <p className="text-sm text-slate-600">
          Enter a topic and configure the research type to begin a multi-agent workflow.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Research Topic
            </label>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={4}
              required
              placeholder="Analyze NVIDIA stock outlook in 2026"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 focus:ring-2"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Research Type
            </label>
            <select
              value={researchType}
              onChange={(e) => setResearchType(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 focus:ring-2"
            >
              {RESEARCH_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700">Depth</label>
            <div className="grid grid-cols-3 gap-3">
              {DEPTH_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setDepth(option.value)}
                  className={`rounded-xl border px-4 py-3 text-sm font-medium transition ${
                    depth === option.value
                      ? "border-brand-600 bg-brand-50 text-brand-700"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <Button type="submit" disabled={loading || topic.trim().length < 3} className="w-full">
            {loading ? "Creating..." : "Create Research Project"}
          </Button>
        </form>
      </Card>

      {loading && <LoadingSpinner label="Creating research project..." />}
    </div>
  );
}
