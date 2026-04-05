import { api } from "@/lib/api-client";
import { OperationalRunForm } from "@/components/operational-run-form";

export default async function NewOperationalRunPage({ searchParams }: { searchParams: { project?: string } }) {
  const project = searchParams.project ? await api.project(searchParams.project).catch(() => null) : null;
  const runs = project ? await api.operationalRuns(project.id).catch(() => []) : [];
  return <OperationalRunForm initial={{ project_id: searchParams.project || "" }} profile={project?.domain_profile} projects={project ? [{ id: project.id, code: project.code, name: project.name, domain_profile: project.domain_profile, run_count: runs.length }] : []} initialProjectId={searchParams.project} />;
}
