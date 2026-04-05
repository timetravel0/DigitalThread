import { api } from "@/lib/api-client";
import { OperationalRunForm } from "@/components/operational-run-form";

export default async function NewOperationalRunPage({ searchParams }: { searchParams: { project?: string } }) {
  const project = searchParams.project ? await api.project(searchParams.project).catch(() => null) : null;
  return <OperationalRunForm initial={{ project_id: searchParams.project || "" }} profile={project?.domain_profile} />;
}
