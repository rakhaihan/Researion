import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import WorkspaceSelector from "../components/workspace/WorkspaceSelector";
import ShareModal from "../components/research/ShareModal";
import VersionsPanel from "../components/research/VersionsPanel";
import CommentsPanel from "../components/research/CommentsPanel";
import PublicReportPage from "../pages/PublicReportPage";

vi.mock("../contexts/WorkspaceContext", () => ({
  useWorkspace: () => ({
    workspaces: [{ id: "ws-1", name: "Default", is_default: true }],
    activeWorkspaceId: "ws-1",
    setActiveWorkspaceId: vi.fn(),
    loading: false,
  }),
}));

vi.mock("../services/api", () => ({
  api: {
    listShareLinks: vi.fn().mockResolvedValue([]),
    createShareLink: vi.fn(),
    listVersions: vi.fn().mockResolvedValue([
      {
        id: "v1",
        version_number: 1,
        created_at: new Date().toISOString(),
        change_reason: "Initial",
        quality_score: 8,
      },
    ]),
    listComments: vi.fn().mockResolvedValue([]),
    getPublicReport: vi.fn().mockResolvedValue({
      title: "Shared",
      markdown_content: "# Hi",
      quality_score: 7,
      quality_status: "passed",
      sources: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      allow_download: false,
    }),
  },
  getPublicApiBase: () => "http://localhost:8000/api",
}));

describe("phase 8 UI", () => {
  it("renders workspace selector", () => {
    render(<WorkspaceSelector />);
    expect(screen.getByLabelText(/workspace/i)).toBeInTheDocument();
  });

  it("renders share modal", () => {
    render(<ShareModal researchId="r1" open onClose={() => {}} />);
    expect(screen.getByText(/share report/i)).toBeInTheDocument();
  });

  it("renders versions panel", async () => {
    render(<VersionsPanel researchId="r1" />);
    expect(await screen.findByText(/version 1/i)).toBeInTheDocument();
  });

  it("renders comments panel", async () => {
    render(<CommentsPanel researchId="r1" />);
    expect(await screen.findByPlaceholderText(/add a comment/i)).toBeInTheDocument();
  });

  it("renders public report page", async () => {
    render(
      <MemoryRouter initialEntries={["/public/reports/test-token"]}>
        <PublicReportPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Shared")).toBeInTheDocument();
  });
});
