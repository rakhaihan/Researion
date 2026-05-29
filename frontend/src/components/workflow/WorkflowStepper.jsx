import { mapWorkflowStepStates } from "../../utils/workflowSteps";
import Badge from "../ui/Badge";

const statusIcon = {
  pending: "○",
  running: "◉",
  completed: "✓",
  failed: "✕",
};

const statusClass = {
  pending: "border-slate-200 bg-white text-slate-400",
  running: "border-brand-500 bg-brand-50 text-brand-700 ring-2 ring-brand-200",
  completed: "border-emerald-500 bg-emerald-50 text-emerald-700",
  failed: "border-red-500 bg-red-50 text-red-700",
};

export default function WorkflowStepper({ progress, projectStatus }) {
  const steps = mapWorkflowStepStates(progress, projectStatus);

  return (
    <ol className="space-y-3" aria-label="Research workflow steps">
      {steps.map((step) => (
        <li key={step.key} className="flex items-start gap-3">
          <span
            className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-sm font-semibold ${statusClass[step.status]}`}
            aria-hidden="true"
          >
            {statusIcon[step.status]}
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-slate-900">{step.label}</span>
              <Badge status={step.status === "running" ? "running" : step.status}>
                {step.status}
              </Badge>
            </div>
            <p className="text-xs text-slate-500">{step.description}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
