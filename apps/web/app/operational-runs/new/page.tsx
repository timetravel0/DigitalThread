import { OperationalRunForm } from "@/components/operational-run-form";

export default function NewOperationalRunPage({ searchParams }: { searchParams: { project?: string } }) {
  return <OperationalRunForm initial={{ project_id: searchParams.project || "" }} />;
}
