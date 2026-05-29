import { Link } from "react-router-dom";
import Button from "../components/Button";
import Card from "../components/Card";

export default function HomePage() {
  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-brand-600 to-indigo-700 p-8 text-white shadow-card">
        <p className="mb-2 text-sm font-medium text-brand-100">Multi-Agent Research Assistant</p>
        <h2 className="mb-4 text-3xl font-bold tracking-tight">
          Automate deep research with AI agents
        </h2>
        <p className="mb-6 max-w-2xl text-brand-100">
          Researion orchestrates specialized agents to plan, search, evaluate sources,
          summarize findings, analyze patterns, critique bias, and produce professional reports.
        </p>
        <Link to="/new">
          <Button className="bg-white text-brand-700 hover:bg-brand-50">
            Start New Research
          </Button>
        </Link>
      </section>

      <section className="grid gap-6 md:grid-cols-3">
        <Card>
          <h3 className="mb-2 font-semibold text-slate-900">7 Specialized Agents</h3>
          <p className="text-sm text-slate-600">
            Planner, Search, Evaluator, Summarizer, Analyst, Critique, and Report Writer work
            together in a LangGraph workflow.
          </p>
        </Card>
        <Card>
          <h3 className="mb-2 font-semibold text-slate-900">Multiple Research Types</h3>
          <p className="text-sm text-slate-600">
            Market, stock/crypto, academic, competitor, and technology trend research modes.
          </p>
        </Card>
        <Card>
          <h3 className="mb-2 font-semibold text-slate-900">Export Ready Reports</h3>
          <p className="text-sm text-slate-600">
            View structured reports in the dashboard and export to Markdown or PDF.
          </p>
        </Card>
      </section>
    </div>
  );
}
