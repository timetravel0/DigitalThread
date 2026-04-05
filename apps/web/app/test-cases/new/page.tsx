import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import { TestCaseForm } from "@/components/test-case-form";

export default async function NewTestCasePage({ searchParams }: { searchParams: { project?: string } }) {
  const project = searchParams.project ? await api.project(searchParams.project).catch(() => null) : null;
  const labels = getLabels(project?.domain_profile);
  return <TestCaseForm initial={{ project_id: searchParams.project || "" }} labels={labels} profile={project?.domain_profile} />;
}
