import { describe, expect, it } from "vitest";
import { mapWorkflowStepStates } from "../utils/workflowSteps";

describe("mapWorkflowStepStates", () => {
  it("marks earlier steps completed when summarizing is active", () => {
    const steps = mapWorkflowStepStates(
      { status: "running", current_step: "summarizing", progress_percentage: 55 },
      "summarizing",
    );
    const planning = steps.find((s) => s.key === "planning");
    const summarizing = steps.find((s) => s.key === "summarizing");
    const analyzing = steps.find((s) => s.key === "analyzing");
    expect(planning.status).toBe("completed");
    expect(summarizing.status).toBe("running");
    expect(analyzing.status).toBe("pending");
  });

  it("marks all steps completed when job completed", () => {
    const steps = mapWorkflowStepStates(
      { status: "completed", current_step: "completed", progress_percentage: 100 },
      "completed",
    );
    expect(steps.every((s) => s.status === "completed")).toBe(true);
  });

  it("marks active step failed when job failed", () => {
    const steps = mapWorkflowStepStates(
      { status: "failed", current_step: "analyzing", progress_percentage: 70 },
      "failed",
    );
    const analyzing = steps.find((s) => s.key === "analyzing");
    expect(analyzing.status).toBe("failed");
  });
});
