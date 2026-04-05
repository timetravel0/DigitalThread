import { api } from "@/lib/api-client";
import { ConnectorForm } from "@/components/connector-form";
import { EmptyState } from "@/components/ui";

export default async function NewConnectorPage({ searchParams }: { searchParams: { project?: string } }) {
  const projects = await api.projects().catch(() => []);
  if (!projects.length) {
    return <EmptyState title="No projects available" description="Create a project first, then register connectors in its scope." />;
  }
  const initialProjectId = searchParams.project && projects.some((project) => project.id === searchParams.project) ? searchParams.project : projects[0].id;
  return <ConnectorForm initial={{ project_id: initialProjectId }} projects={projects} initialProjectId={initialProjectId} />;
}
