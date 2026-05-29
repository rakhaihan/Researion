import { useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import Button from "../ui/Button";
import Card from "../ui/Card";
import { downloadExport } from "../../services/api";

function renderWithCitations(children, onCitationClick) {
  const nodes = Array.isArray(children) ? children : [children];
  return nodes.map((child, i) => {
    if (typeof child !== "string" || !/\[S\d+\]/.test(child)) {
      return <span key={i}>{child}</span>;
    }
    return child.split(/(\[S\d+\])/).map((part, j) => {
      if (!/^\[S\d+\]$/.test(part)) {
        return <span key={`${i}-${j}`}>{part}</span>;
      }
      return (
        <CitationLink key={`${i}-${j}`} onCitationClick={onCitationClick}>
          {part}
        </CitationLink>
      );
    });
  });
}

function CitationLink({ children, onCitationClick }) {
  const text = String(children);
  const match = text.match(/^\[S\d+\]$/);
  if (match && onCitationClick) {
    return (
      <button
        type="button"
        className="mx-0.5 rounded bg-brand-100 px-1 py-0.5 text-xs font-semibold text-brand-800 hover:bg-brand-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
        onClick={() => onCitationClick(text.replace(/[[\]]/g, ""))}
      >
        {text}
      </button>
    );
  }
  return <span>{children}</span>;
}

export default function ReportViewer({ researchId, markdownContent, onCitationClick }) {
  const [exporting, setExporting] = useState(null);
  const [copyMsg, setCopyMsg] = useState("");

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(markdownContent);
      setCopyMsg("Copied to clipboard");
      setTimeout(() => setCopyMsg(""), 2000);
    } catch {
      setCopyMsg("Copy failed");
    }
  }

  async function handleExport(format) {
    setExporting(format);
    try {
      await downloadExport(researchId, format);
    } finally {
      setExporting(null);
    }
  }

  if (!markdownContent) return null;

  return (
    <Card padding={false} className="overflow-hidden">
      <div className="sticky top-14 z-20 flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-white/95 px-4 py-3 backdrop-blur sm:px-6">
        <h3 className="font-semibold text-slate-900">Final Report</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" size="sm" onClick={handleCopy}>
            Copy Markdown
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={exporting === "markdown"}
            onClick={() => handleExport("markdown")}
          >
            {exporting === "markdown" ? "Exporting…" : "Export Markdown"}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={exporting === "pdf"}
            onClick={() => handleExport("pdf")}
          >
            {exporting === "pdf" ? "Exporting…" : "Export PDF"}
          </Button>
        </div>
      </div>
      {copyMsg && (
        <p className="border-b border-slate-100 bg-brand-50 px-4 py-2 text-xs text-brand-800">{copyMsg}</p>
      )}
      <div className="markdown-body prose prose-slate max-w-none px-4 py-6 sm:px-6">
        <ReactMarkdown
          rehypePlugins={[rehypeSanitize]}
          components={{
            p: ({ children }) => <p>{renderWithCitations(children, onCitationClick)}</p>,
            li: ({ children }) => <li>{renderWithCitations(children, onCitationClick)}</li>,
          }}
        >
          {markdownContent}
        </ReactMarkdown>
      </div>
    </Card>
  );
}
