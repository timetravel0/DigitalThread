import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function ConnectorPage({ params }: { params: { id: string } }) {
  const data = await api.connector(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Connector not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.connector.name}
        description={data.connector.description || "Authoritative external source connector"}
        action={<Button href={`/connectors/${data.connector.id}/edit`} variant="secondary">Edit connector</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">Connector definition</div></CardHeader>
          <CardBody className="space-y-3">
            <Row label="Type" value={data.connector.connector_type} />
            <Row label="Status" value={<Badge tone={data.connector.is_active ? "success" : "neutral"}>{data.connector.is_active ? "active" : "inactive"}</Badge>} />
            <Row label="Base URL" value={data.connector.base_url || "None"} />
            <Row label="Artifacts" value={data.connector.artifact_count || 0} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Federated artifacts</div></CardHeader>
          <CardBody className="space-y-3">
            {data.artifacts.length ? (
              data.artifacts.map((artifact: any) => (
                <Link key={artifact.id} href={`/external-artifacts/${artifact.id}`} className="block rounded-xl border border-line bg-panel2 p-3 hover:border-accent/50">
                  <div className="font-medium">{artifact.external_id}</div>
                  <div className="text-sm text-muted">{artifact.name}</div>
                </Link>
              ))
            ) : (
              <div className="text-sm text-muted">No external artifacts linked to this connector.</div>
            )}
          </CardBody>
        </Card>
      </div>
      <Link href={`/projects/${data.connector.project_id}/authoritative-sources?tab=connectors`} className="text-sm text-accent">Back to authoritative sources</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}
