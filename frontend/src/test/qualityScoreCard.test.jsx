import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import QualityScoreCard from "../components/research/QualityScoreCard";

describe("QualityScoreCard", () => {
  it("renders overall score and breakdown", () => {
    render(
      <QualityScoreCard
        qualityEvaluation={{
          overall_score: 72,
          quality_status: "warning",
          citation_score: 80,
          source_diversity_score: 65,
          source_credibility_score: 70,
          freshness_score: 60,
          completeness_score: 85,
          warnings: ["Low citation coverage on key findings."],
          recommendations: ["Add more citations."],
          citation_validation: { invalid_citations: ["S9"] },
        }}
        qualityStatus="warning"
        qualityScore={72}
        warnings={["Low citation coverage on key findings."]}
        recommendations={["Add more citations."]}
        onRegenerate={vi.fn()}
      />,
    );

    expect(screen.getByText("Research quality")).toBeInTheDocument();
    expect(screen.getByText("72")).toBeInTheDocument();
    expect(screen.getByText(/fictitious citations/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /regenerate report/i })).toBeInTheDocument();
  });
});
