export const SOURCE_MODES = [
  { value: "web_only", label: "Web only", hint: "Live search via Tavily (or mock)" },
  { value: "documents_only", label: "Documents only", hint: "RAG from your knowledge base" },
  { value: "hybrid", label: "Hybrid", hint: "Web search plus uploaded documents" },
];

export function validateResearchSource({ researchSourceMode, selectedDocumentIds }) {
  const errors = {};
  if (
    (researchSourceMode === "documents_only" || researchSourceMode === "hybrid") &&
    selectedDocumentIds.length === 0
  ) {
    errors.documents = "Select at least one processed document.";
  }
  return errors;
}
