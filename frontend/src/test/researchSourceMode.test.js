import { describe, expect, it } from "vitest";
import { SOURCE_MODES, validateResearchSource } from "../utils/researchSourceConfig";

describe("research source mode", () => {
  it("defines web, documents, and hybrid modes", () => {
    const values = SOURCE_MODES.map((m) => m.value);
    expect(values).toEqual(["web_only", "documents_only", "hybrid"]);
  });

  it("requires documents for hybrid and documents_only", () => {
    expect(
      validateResearchSource({ researchSourceMode: "hybrid", selectedDocumentIds: [] }).documents,
    ).toBeTruthy();
    expect(
      validateResearchSource({
        researchSourceMode: "documents_only",
        selectedDocumentIds: [],
      }).documents,
    ).toBeTruthy();
  });

  it("allows web_only without documents", () => {
    const errors = validateResearchSource({
      researchSourceMode: "web_only",
      selectedDocumentIds: [],
    });
    expect(Object.keys(errors)).toHaveLength(0);
  });
});
