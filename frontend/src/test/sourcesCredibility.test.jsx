import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import SourcesPanel from "../components/research/SourcesPanel";

const sources = [
  {
    id: "1",
    citation_key: "S1",
    title: "High trust source",
    url: "https://example.com/a",
    snippet: "Snippet",
    credibility_score: 9,
    credibility_tier: "high",
    credibility_reason: "Reputable domain",
    source_type: "news",
  },
  {
    id: "2",
    citation_key: "S2",
    title: "Low trust source",
    url: "https://example.com/b",
    snippet: "Snippet",
    credibility_score: 2,
    credibility_tier: "low",
    credibility_reason: "Unverified blog",
    source_type: "blog",
  },
];

describe("SourcesPanel credibility", () => {
  it("shows tier badges and low credibility warning", () => {
    render(<SourcesPanel sources={sources} showWarning />);
    expect(screen.getByText("S1")).toBeInTheDocument();
    expect(screen.getByText(/low credibility sources/i)).toBeInTheDocument();
  });

  it("filters to high credibility only", async () => {
    render(<SourcesPanel sources={sources} />);
    fireEvent.click(screen.getByRole("button", { name: /high credibility/i }));
    await waitFor(() => {
      expect(screen.getByText("High trust source")).toBeInTheDocument();
      expect(screen.queryByText("Low trust source")).not.toBeInTheDocument();
    });
  });
});
