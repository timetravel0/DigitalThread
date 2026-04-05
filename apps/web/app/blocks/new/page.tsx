import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import { BlockForm } from "@/components/block-form";

export default async function NewBlockPage({ searchParams }: { searchParams: { project?: string } }) {
  const project = searchParams.project ? await api.project(searchParams.project).catch(() => null) : null;
  const labels = getLabels(project?.domain_profile);
  return <BlockForm initial={{ project_id: searchParams.project || "" }} labels={labels} />;
}
