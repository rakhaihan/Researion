import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import Input from "../components/ui/Input";
import Select from "../components/ui/Select";
import Alert from "../components/ui/Alert";
import PageHeader from "../components/ui/PageHeader";
import { api } from "../services/api";
import {
  DEPTH_OPTIONS,
  RESEARCH_TYPES,
  TOPIC_PLACEHOLDERS,
  TYPE_TEMPLATES,
} from "../utils/researchConfig";

export default function NewResearchPage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState("");
  const [researchType, setResearchType] = useState("");
  const [depth, setDepth] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const placeholder = useMemo(
    () => TOPIC_PLACEHOLDERS[researchType] || "Describe what you want to research in detail…",
    [researchType],
  );

  function validate() {
    const errors = {};
    if (topic.trim().length < 10) {
      errors.topic = "Topic must be at least 10 characters.";
    }
    if (!researchType) {
      errors.researchType = "Select a research type.";
    }
    if (!depth) {
      errors.depth = "Select a research depth.";
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setError("");

    try {
      const project = await api.createResearch({
        topic: topic.trim(),
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
      <PageHeader
        title="New Research"
        description="Choose a template, set depth, and describe your topic. You will be redirected to the detail page after creation."
      />

      <div className="grid gap-3 sm:grid-cols-2">
        {RESEARCH_TYPES.map((type) => {
          const template = TYPE_TEMPLATES[type];
          const selected = researchType === type;
          return (
            <button
              key={type}
              type="button"
              onClick={() => setResearchType(type)}
              className={`rounded-2xl border p-4 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                selected
                  ? "border-brand-500 bg-brand-50"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <p className="font-semibold text-slate-900">{template.title}</p>
              <p className="mt-1 text-xs text-slate-600">{template.description}</p>
            </button>
          );
        })}
      </div>
      {fieldErrors.researchType && (
        <p className="text-xs text-red-600" role="alert">
          {fieldErrors.researchType}
        </p>
      )}

      <Card>
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <Input
            label="Research topic"
            name="topic"
            textarea
            rows={4}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder={placeholder}
            error={fieldErrors.topic}
            hint={`${topic.trim().length}/10 characters minimum`}
          />

          <Select
            label="Research type"
            name="researchType"
            value={researchType}
            onChange={(e) => setResearchType(e.target.value)}
            error={fieldErrors.researchType}
          >
            <option value="">Select type…</option>
            {RESEARCH_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>

          <div>
            <p className="mb-2 text-sm font-medium text-slate-700">Depth</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {DEPTH_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setDepth(option.value)}
                  className={`rounded-xl border px-4 py-3 text-left text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
                    depth === option.value
                      ? "border-brand-600 bg-brand-50 text-brand-800"
                      : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                  }`}
                >
                  <span className="block font-semibold">{option.label}</span>
                  <span className="mt-1 block text-xs text-slate-500">{option.hint}</span>
                </button>
              ))}
            </div>
            {fieldErrors.depth && (
              <p className="mt-1.5 text-xs text-red-600" role="alert">
                {fieldErrors.depth}
              </p>
            )}
          </div>

          {error && <Alert variant="error">{error}</Alert>}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating…" : "Create research project"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
