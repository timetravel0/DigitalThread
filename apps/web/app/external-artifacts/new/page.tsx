import { api } from "@/lib/api-client";
import { ExternalArtifactForm } from "@/components/external-artifact-form";
import { EmptyState } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function NewExternalArtifactPage({ searchParams }: { searchParams: { project?: string } }) {
  const projects = await api.projects().catch(() => []);
  if (!projects.length) {
    return <EmptyState title="No projects available" description="Create a project first, then register external artifacts in its scope." />;
  }
  const initialProjectId = searchParams.project && projects.some((project) => project.id === searchParams.project) ? searchParams.project : projects[0].id;
  const connectors = await api.connectors(initialProjectId).catch(() => []);
  return <ExternalArtifactForm initial={{ project_id: initialProjectId }} connectors={connectors} projects={projects} initialProjectId={initialProjectId} />;
}
