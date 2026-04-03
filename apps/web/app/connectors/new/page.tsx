import { ConnectorForm } from "@/components/connector-form";
import { EmptyState } from "@/components/ui";

export default async function NewConnectorPage({ searchParams }: { searchParams: { project?: string } }) {
  if (!searchParams.project) {
    return <EmptyState title="Project missing" description="Open the page from a project workspace so the connector can be registered in the correct scope." />;
  }
  return <ConnectorForm initial={{ project_id: searchParams.project }} />;
}
