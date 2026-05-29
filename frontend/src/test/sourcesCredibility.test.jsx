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

const documentSource = {
  id: "3",
  citation_key: "S3",
  title: "brief.pdf, page 2",
  url: "document://doc-id/chunk/chunk-id",
  snippet: "Internal excerpt",
  credibility_score: 7,
  credibility_tier: "medium",
  source_type: "document",
  page_number: 2,
};

describe("SourcesPanel credibility", () => {
  it("shows Web and Document badges", () => {
    render(<SourcesPanel sources={[sources[0], documentSource]} />);
    expect(screen.getByText("Web")).toBeInTheDocument();
    expect(screen.getByText("Document")).toBeInTheDocument();
    expect(screen.getByText("Page 2")).toBeInTheDocument();
  });

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
