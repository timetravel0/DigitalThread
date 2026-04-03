import { TestCaseForm } from "@/components/test-case-form";

export default function NewTestCasePage({ searchParams }: { searchParams: { project?: string } }) {
  return <TestCaseForm initial={{ project_id: searchParams.project || "" }} />;
}
