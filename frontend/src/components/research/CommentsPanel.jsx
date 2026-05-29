import { useEffect, useState } from "react";
import Button from "../ui/Button";
import Alert from "../ui/Alert";
import { api } from "../../services/api";

export default function CommentsPanel({ researchId, anchorRef }) {
  const [comments, setComments] = useState([]);
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await api.listComments(researchId);
      setComments(data);
    } catch {
      setComments([]);
    }
  }

  useEffect(() => {
    load();
  }, [researchId]);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!content.trim()) return;
    try {
      await api.createComment(researchId, {
        content: content.trim(),
        anchor_type: anchorRef ? "source" : "general",
        anchor_ref: anchorRef || null,
      });
      setContent("");
      await load();
    } catch (err) {
      setError(err.message || "Failed to post comment");
    }
  }

  return (
    <div className="space-y-4">
      {error && <Alert variant="error">{error}</Alert>}
      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={3}
          placeholder="Add a comment…"
          className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm"
        />
        <Button type="submit" size="sm">
          Post comment
        </Button>
      </form>
      <ul className="space-y-3">
        {comments.map((c) => (
          <li key={c.id} className="rounded-xl bg-slate-50 p-3 text-sm">
            <p className="font-medium text-slate-800">{c.author_name || "User"}</p>
            {c.anchor_ref && (
              <p className="text-xs text-brand-600">Ref: {c.anchor_ref}</p>
            )}
            <p className="mt-1 text-slate-700">{c.content}</p>
            <p className="mt-1 text-xs text-slate-500">
              {new Date(c.created_at).toLocaleString()}
            </p>
            {c.replies?.map((r) => (
              <div key={r.id} className="ml-4 mt-2 border-l-2 border-slate-200 pl-3">
                <p className="font-medium text-slate-700">{r.author_name}</p>
                <p className="text-slate-600">{r.content}</p>
              </div>
            ))}
          </li>
        ))}
      </ul>
    </div>
  );
}
