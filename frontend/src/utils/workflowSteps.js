export const WORKFLOW_STEPS = [
  {
    key: "planning",
    label: "Planning",
    description: "Breaking the topic into focused research questions.",
    order: 0,
  },
  {
    key: "searching",
    label: "Searching",
    description: "Collecting sources from the web via search APIs.",
    order: 1,
  },
  {
    key: "evaluating_sources",
    label: "Evaluating Sources",
    description: "Scoring credibility and relevance of each source.",
    order: 2,
  },
  {
    key: "summarizing",
    label: "Summarizing",
    description: "Extracting key points with citation keys.",
    order: 3,
  },
  {
    key: "analyzing",
    label: "Analyzing",
    description: "Synthesizing patterns, risks, and opportunities.",
    order: 4,
  },
  {
    key: "critiquing",
    label: "Critiquing",
    description: "Checking bias, gaps, and weak citations.",
    order: 5,
  },
  {
    key: "writing_report",
    label: "Writing Report",
    description: "Composing the final citation-aware report.",
    order: 6,
  },
  {
    key: "completed",
    label: "Completed",
    description: "Research workflow finished successfully.",
    order: 7,
  },
];

const STEP_INDEX = Object.fromEntries(WORKFLOW_STEPS.map((s, i) => [s.key, i]));

const RESEARCH_STATUS_TO_STEP = {
  queued: "planning",
  planning: "planning",
  searching: "searching",
  evaluating: "evaluating_sources",
  summarizing: "summarizing",
  analyzing: "analyzing",
  critiquing: "critiquing",
  writing: "writing_report",
  completed: "completed",
  failed: null,
};

export function resolveActiveStepKey(progress, projectStatus) {
  if (progress?.current_step) return progress.current_step;
  if (projectStatus && RESEARCH_STATUS_TO_STEP[projectStatus]) {
    return RESEARCH_STATUS_TO_STEP[projectStatus];
  }
  return null;
}

export function mapWorkflowStepStates(progress, projectStatus) {
  const jobStatus = progress?.status;
  const failed = jobStatus === "failed" || projectStatus === "failed";
  const completed = jobStatus === "completed" || projectStatus === "completed";
  const activeKey = resolveActiveStepKey(progress, projectStatus);
  const activeIndex = activeKey != null ? STEP_INDEX[activeKey] ?? -1 : -1;

  return WORKFLOW_STEPS.map((step) => {
    const idx = step.order;
    let status = "pending";

    if (failed && activeIndex >= 0 && idx === activeIndex) {
      status = "failed";
    } else if (completed) {
      status = "completed";
    } else if (activeIndex >= 0) {
      if (idx < activeIndex) status = "completed";
      else if (idx === activeIndex) status = jobStatus === "queued" ? "pending" : "running";
      else status = "pending";
    } else if (jobStatus === "queued") {
      status = idx === 0 ? "pending" : "pending";
    }

    return { ...step, status };
  });
}

export function getStageDescription(progress, projectStatus) {
  const activeKey = resolveActiveStepKey(progress, projectStatus);
  const step = WORKFLOW_STEPS.find((s) => s.key === activeKey);
  if (progress?.current_step_label) return progress.current_step_label;
  if (step) return step.description;
  if (progress?.status === "queued") return "Waiting for a worker to pick up this job.";
  return "Workflow progress will appear when you run research.";
}
