import { BlockForm } from "@/components/block-form";

export default function NewBlockPage({ searchParams }: { searchParams: { project?: string } }) {
  return <BlockForm initial={{ project_id: searchParams.project || "" }} />;
}
