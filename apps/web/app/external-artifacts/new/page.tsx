import { api } from "@/lib/api-client";
import { ExternalArtifactForm } from "@/components/external-artifact-form";
import { EmptyState } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function NewExternalArtifactPage({ searchParams }: { searchParams: { project?: string } }) {
  if (!searchParams.project) {
    return <EmptyState title="Project missing" description="Open the page from a project workspace so the artifact can be registered in the correct scope." />;
  }
  const connectors = await api.connectors(searchParams.project).catch(() => []);
  return <ExternalArtifactForm initial={{ project_id: searchParams.project }} connectors={connectors} />;
}
