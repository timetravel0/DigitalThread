import { ConfigurationContextForm } from "@/components/configuration-context-form";
import { EmptyState } from "@/components/ui";

export const dynamic = "force-dynamic";

export default function NewConfigurationContextPage({ searchParams }: { searchParams: { project?: string } }) {
  if (!searchParams.project) {
    return <EmptyState title="Project missing" description="Open the page from a project workspace so the configuration context can be registered in the correct scope." />;
  }
  return <ConfigurationContextForm initial={{ project_id: searchParams.project }} />;
}
