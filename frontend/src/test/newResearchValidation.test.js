import { describe, expect, it } from "vitest";
import { TOPIC_PLACEHOLDERS } from "../utils/researchConfig";

function validateForm({ topic, researchType, depth }) {
  const errors = {};
  if (topic.trim().length < 10) errors.topic = "Topic must be at least 10 characters.";
  if (!researchType) errors.researchType = "Select a research type.";
  if (!depth) errors.depth = "Select a research depth.";
  return errors;
}

describe("new research validation", () => {
  it("requires topic of at least 10 characters", () => {
    const errors = validateForm({
      topic: "short",
      researchType: "Market Research",
      depth: "standard",
    });
    expect(errors.topic).toBeTruthy();
  });

  it("requires research type and depth", () => {
    const errors = validateForm({ topic: "A long enough topic here", researchType: "", depth: "" });
    expect(errors.researchType).toBeTruthy();
    expect(errors.depth).toBeTruthy();
  });

  it("passes with valid input", () => {
    const errors = validateForm({
      topic: "Analyze the EV market in Southeast Asia",
      researchType: "Market Research",
      depth: "deep",
    });
    expect(Object.keys(errors)).toHaveLength(0);
  });

  it("provides dynamic placeholders per type", () => {
    expect(TOPIC_PLACEHOLDERS["Academic Research"]).toContain("Literature");
  });
});
