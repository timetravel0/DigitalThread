import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import { RequirementForm } from "@/components/requirement-form";

export default async function NewRequirementPage({ searchParams }: { searchParams: { project?: string } }) {
  const project = searchParams.project ? await api.project(searchParams.project).catch(() => null) : null;
  const labels = getLabels(project?.domain_profile);
  return <RequirementForm initial={{ project_id: searchParams.project || "" }} labels={labels} />;
}
