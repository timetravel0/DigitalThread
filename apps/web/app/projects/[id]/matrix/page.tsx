import Link from "next/link";
import { api } from "@/lib/api-client";
import { Button, SectionTitle } from "@/components/ui";
import { MatrixGrid } from "@/components/matrix-grid";

export const dynamic = "force-dynamic";

export default async function ProjectMatrixPage({ params, searchParams }: { params: { id: string }; searchParams?: { mode?: string; status?: string; category?: string } }) {
  const mode = searchParams?.mode === "tests" ? "tests" : "components";
  const data = await api.matrix(params.id, mode as "components" | "tests", { status: searchParams?.status, category: searchParams?.category }).catch(() => null);

  if (!data) {
    return <div className="text-sm text-muted">Matrix unavailable until the backend is running.</div>;
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Traceability Matrix"
        description="Rows are requirements. Columns switch between components and test cases."
        action={
          <div className="flex gap-2">
            <Button href={`/projects/${params.id}/matrix?mode=components`} variant={mode === "components" ? "primary" : "secondary"}>Components</Button>
            <Button href={`/projects/${params.id}/matrix?mode=tests`} variant={mode === "tests" ? "primary" : "secondary"}>Tests</Button>
          </div>
        }
      />
      <MatrixGrid data={data} />
      <div className="text-sm text-muted">
        Use filters via the API response and add matrix filter controls later if you want a richer analytical workflow.
      </div>
      <Link className="text-sm text-accent" href={`/projects/${params.id}`}>
        Back to project overview
      </Link>
    </div>
  );
}

