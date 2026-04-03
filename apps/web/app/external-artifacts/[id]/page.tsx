import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { ExternalArtifactVersionForm } from "@/components/external-artifact-version-form";

export const dynamic = "force-dynamic";

export default async function ExternalArtifactPage({ params }: { params: { id: string } }) {
  const data = await api.externalArtifact(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">External artifact not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${data.external_artifact.external_id} - ${data.external_artifact.name}`}
        description={data.external_artifact.description || "Authoritative external artifact"}
        action={<Button href={`/external-artifacts/${data.external_artifact.id}/edit`} variant="secondary">Edit artifact</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">External artifact</div></CardHeader>
          <CardBody className="space-y-3">
            <Row label="Type" value={data.external_artifact.artifact_type} />
            <Row label="Status" value={<Badge tone={data.external_artifact.status === "active" ? "success" : data.external_artifact.status === "deprecated" ? "warning" : "danger"}>{data.external_artifact.status}</Badge>} />
            <Row label="Connector" value={data.external_artifact.connector_name || "None"} />
            <Row label="Canonical URI" value={data.external_artifact.canonical_uri || "None"} />
            <Row label="Native URL" value={data.external_artifact.native_tool_url || "None"} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Version register</div></CardHeader>
          <CardBody className="space-y-3">
            {data.versions.length ? (
              data.versions.map((version: any) => (
                <div key={version.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{version.version_label}</div>
                  <div className="text-xs text-muted">{version.revision_label || "No revision"} · {version.created_at}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No versions recorded.</div>
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="text-sm font-medium">Add version</div>
              <div className="mt-3">
                <ExternalArtifactVersionForm artifactId={data.external_artifact.id} />
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Linked external source usage</div></CardHeader>
        <CardBody className="space-y-3">
          {data.artifact_links.length ? (
            data.artifact_links.map((link: any) => (
              <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{link.internal_object_label || link.internal_object_type} <span className="text-muted">→</span> {link.external_artifact_name}</div>
                <div className="text-xs text-muted">{link.relation_type} · {link.external_artifact_version_label || "unpinned"}</div>
              </div>
            ))
          ) : (
            <div className="text-sm text-muted">No artifact links recorded yet.</div>
          )}
        </CardBody>
      </Card>

      <Link href={`/projects/${data.external_artifact.project_id}/authoritative-sources?tab=external-artifacts`} className="text-sm text-accent">Back to authoritative sources</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}
