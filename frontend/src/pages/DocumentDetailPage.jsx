import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Badge from "../components/ui/Badge";
import Card from "../components/ui/Card";
import Alert from "../components/ui/Alert";
import { SkeletonList } from "../components/ui/Skeleton";
import { api } from "../services/api";

export default function DocumentDetailPage() {
  const { id } = useParams();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const data = await api.getDocument(id);
      setDoc(data);
    } catch (err) {
      setError(err.message || "Failed to load document");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!doc || (doc.status !== "uploaded" && doc.status !== "processing")) return undefined;
    const timer = setInterval(load, 2500);
    return () => clearInterval(timer);
  }, [doc, load]);

  if (loading) return <SkeletonList count={2} />;
  if (!doc) return <Alert variant="error">{error || "Document not found"}</Alert>;

  return (
    <div className="space-y-6">
      <Link to="/documents" className="text-sm text-brand-600 hover:underline">
        ← Back to Knowledge Base
      </Link>
      <Card>
        <div className="mb-3 flex flex-wrap gap-2">
          <Badge status={doc.status}>{doc.status}</Badge>
          {doc.processing_step && (
            <span className="text-xs text-slate-500">Step: {doc.processing_step}</span>
          )}
        </div>
        <h2 className="text-xl font-bold text-slate-900">{doc.original_filename}</h2>
        <dl className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
          <div>
            <dt className="font-medium text-slate-700">Content type</dt>
            <dd>{doc.content_type}</dd>
          </div>
          <div>
            <dt className="font-medium text-slate-700">Chunks</dt>
            <dd>{doc.chunk_count}</dd>
          </div>
          <div>
            <dt className="font-medium text-slate-700">Created</dt>
            <dd>{new Date(doc.created_at).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="font-medium text-slate-700">Updated</dt>
            <dd>{new Date(doc.updated_at).toLocaleString()}</dd>
          </div>
        </dl>
        {doc.error_message && (
          <Alert variant="error" className="mt-4">
            {doc.error_message}
          </Alert>
        )}
      </Card>
    </div>
  );
}
