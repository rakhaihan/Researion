import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import DocumentsPage from "../pages/DocumentsPage";

vi.mock("../services/api", () => ({
  api: {
    listDocuments: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
  },
}));

import { api } from "../services/api";

describe("DocumentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders knowledge base header and empty state", async () => {
    api.listDocuments.mockResolvedValue([]);
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText("Knowledge Base")).toBeInTheDocument();
    expect(screen.getByText(/no documents yet/i)).toBeInTheDocument();
  });

  it("lists documents with status badge", async () => {
    api.listDocuments.mockResolvedValue([
      {
        id: "1",
        original_filename: "notes.txt",
        status: "processed",
        file_size: 1200,
        chunk_count: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]);
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText("notes.txt")).toBeInTheDocument();
    expect(screen.getByText("processed")).toBeInTheDocument();
  });
});
