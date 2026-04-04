import Link from "next/link";
import { DOCS } from "@/lib/docs";
import { Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default function DocumentationIndexPage() {
  return (
    <div className="space-y-6">
      <SectionTitle
        title="Documentation"
        description="Repository documentation is available inside the application as a built-in manual."
      />
      <Card>
        <CardBody className="space-y-3 text-sm text-muted">
          <p>
            This section reads the documentation stored in the repository and makes it available from the application itself.
          </p>
          <p>
            Use the <span className="text-text">User Guide</span> for task-oriented instructions and the <span className="text-text">Platform Logic Guide</span> for the internal operating model.
          </p>
        </CardBody>
      </Card>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {DOCS.map((doc) => (
          <Link key={doc.slug} href={`/docs/${doc.slug}`} className="rounded-2xl border border-line bg-panel p-5 hover:border-accent/50">
            <div className="text-xs uppercase tracking-[0.25em] text-muted">Manual</div>
            <div className="mt-2 text-lg font-semibold text-text">{doc.title}</div>
            <div className="mt-2 text-sm text-muted">{doc.description}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
