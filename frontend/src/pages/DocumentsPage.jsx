import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import PageHeader from "../components/ui/PageHeader";
import Alert from "../components/ui/Alert";
import EmptyState from "../components/ui/EmptyState";
import { SkeletonList } from "../components/ui/Skeleton";
import { api } from "../services/api";

const STATUS_VARIANT = {
  uploaded: "queued",
  processing: "running",
  processed: "completed",
  failed: "failed",
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    try {
      const data = await api.listDocuments();
      setDocuments(data);
    } catch (err) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  useEffect(() => {
    const hasProcessing = documents.some(
      (d) => d.status === "uploaded" || d.status === "processing",
    );
    if (!hasProcessing) return undefined;
    const timer = setInterval(loadDocuments, 3000);
    return () => clearInterval(timer);
  }, [documents, loadDocuments]);

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadDocument(file);
      await loadDocuments();
    } catch (err) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this document and all chunks?")) return;
    try {
      await api.deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      setError(err.message || "Delete failed");
    }
  }

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge Base"
        description="Upload PDF, TXT, or Markdown files. Processed documents can power document-only or hybrid research."
        actions={
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".pdf,.txt,.md,.markdown"
              className="sr-only"
              onChange={handleUpload}
              disabled={uploading}
            />
            <span className="inline-flex rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
              {uploading ? "Uploading…" : "Upload document"}
            </span>
          </label>
        }
      />

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <SkeletonList count={3} />
      ) : documents.length === 0 ? (
        <EmptyState
          title="No documents yet"
          description="Upload a PDF, TXT, or Markdown file to build your personal knowledge base."
        />
      ) : (
        <div className="space-y-4">
          {documents.map((doc) => (
            <Card key={doc.id}>
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="mb-2 flex flex-wrap gap-2">
                    <Badge status={STATUS_VARIANT[doc.status] || "pending"}>
                      {doc.status}
                    </Badge>
                    <span className="text-xs text-slate-500">{formatSize(doc.file_size)}</span>
                    {doc.chunk_count > 0 && (
                      <span className="text-xs text-slate-500">{doc.chunk_count} chunks</span>
                    )}
                  </div>
                  <h3 className="font-semibold text-slate-900">{doc.original_filename}</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    Uploaded {new Date(doc.created_at).toLocaleString()}
                  </p>
                  {doc.error_message && (
                    <p className="mt-2 text-sm text-red-600">{doc.error_message}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Link to={`/documents/${doc.id}`}>
                    <Button variant="secondary" size="sm">
                      Details
                    </Button>
                  </Link>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(doc.id)}>
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
