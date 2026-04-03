import { api } from "@/lib/api-client";
import { ConnectorForm } from "@/components/connector-form";

export const dynamic = "force-dynamic";

export default async function EditConnectorPage({ params }: { params: { id: string } }) {
  const data = await api.connector(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Connector not found.</div>;
  return <ConnectorForm initial={data.connector} />;
}
