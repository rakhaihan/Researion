export const RESEARCH_TYPES = [
  "Market Research",
  "Stock/Crypto Research",
  "Academic Research",
  "Competitor Analysis",
  "Technology Trend Analysis",
];

export const DEPTH_OPTIONS = [
  { value: "quick", label: "Quick", hint: "Faster run with fewer sources." },
  { value: "standard", label: "Standard", hint: "Balanced depth for most topics." },
  { value: "deep", label: "Deep", hint: "More thorough analysis and sources." },
];

export const TOPIC_PLACEHOLDERS = {
  "Market Research": "Analyze the EV battery market in Southeast Asia for 2026",
  "Stock/Crypto Research": "Analyze NVIDIA stock outlook and risks for 2026",
  "Academic Research": "Literature review on transformer efficiency in edge devices",
  "Competitor Analysis": "Compare Notion vs Obsidian for knowledge management teams",
  "Technology Trend Analysis": "Emerging AI agent frameworks for enterprise automation",
};

export const TYPE_TEMPLATES = {
  "Market Research": {
    title: "Market Research",
    description: "Industry size, drivers, competition, and outlook.",
  },
  "Stock/Crypto Research": {
    title: "Stock/Crypto Research",
    description: "Fundamentals, catalysts, risks, and sentiment.",
  },
  "Academic Research": {
    title: "Academic Research",
    description: "Scholarly sources, methods, and synthesis.",
  },
  "Competitor Analysis": {
    title: "Competitor Analysis",
    description: "Positioning, strengths, weaknesses, moats.",
  },
  "Technology Trend Analysis": {
    title: "Technology Trend Analysis",
    description: "Adoption curves, innovations, and forecasts.",
  },
};

export const RUNNING_STATUSES = new Set([
  "queued",
  "planning",
  "searching",
  "evaluating",
  "summarizing",
  "analyzing",
  "critiquing",
  "writing",
]);

export const ACTIVE_JOB_STATUSES = new Set(["queued", "running"]);
