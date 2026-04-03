import { RequirementForm } from "@/components/requirement-form";

export default function NewRequirementPage({ searchParams }: { searchParams: { project?: string } }) {
  return <RequirementForm initial={{ project_id: searchParams.project || "" }} />;
}
