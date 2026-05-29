import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";

export default function SharedReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Shared Reports"
        description="Create share links from any completed research detail page. Active links you created appear on that research's Share modal."
      />
      <Card>
        <p className="text-sm text-slate-600">
          Open a research project with a completed report, click <strong>Share</strong>, and copy
          the public link. Recipients can view the report at{" "}
          <code className="rounded bg-slate-100 px-1">/public/reports/:token</code> without logging
          in.
        </p>
      </Card>
    </div>
  );
}
