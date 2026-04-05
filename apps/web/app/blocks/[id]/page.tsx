import Link from "next/link";
import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import { ArtifactLinkForm } from "@/components/artifact-link-form";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";
import { ViewCue } from "@/components/view-cue";

export const dynamic = "force-dynamic";

export default async function BlockPage({ params }: { params: { id: string } }) {
  const data = await api.block(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Block not found.</div>;
  const project = await api.project(data.block.project_id).catch(() => null);
  const labels = getLabels(project?.domain_profile);
  const artifacts = await api.externalArtifacts(data.block.project_id).catch(() => []);

  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.block.key} - ${data.block.name}`} description={data.block.description} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="font-semibold">{labels.block} (SysML-inspired structural element)</div>
              <div className="flex flex-wrap gap-2">
                {data.block.status === "approved" || data.block.status === "in_review" ? null : (
                  <Button href={`/blocks/${data.block.id}/edit`} variant="secondary">Edit</Button>
                )}
                <WorkflowActions kind="block" id={data.block.id} status={data.block.status} />
              </div>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            <Row label="Kind" value={data.block.block_kind} />
            <Row label="Abstraction" value={<Badge tone={data.block.abstraction_level === "physical" ? "warning" : "accent"}>{data.block.abstraction_level}</Badge>} />
            <Row label="Status" value={<Badge>{data.block.status}</Badge>} />
            <Row label="Version" value={data.block.version} />
            <Row label="Owner" value={data.block.owner || "None"} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Impact preview</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.impact.likely_impacted || []).slice(0, 8).map((item: any) => (
              <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{item.label}</div>
                <div className="text-xs text-muted">{item.object_type}</div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <ViewCue layer={data.block.abstraction_level} />

      {data.block.status === "approved" ? (
        <Card>
          <CardHeader><div className="font-semibold">Approved item editing</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This {labels.block.toLowerCase()} is approved and cannot be edited in place.</p>
            <p>Create a draft version to continue modeling the {labels.block.toLowerCase()} without losing history.</p>
            <WorkflowActions kind="block" id={data.block.id} status={data.block.status} />
          </CardBody>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Containment</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.containments || []).map((rel: any) => (
              <div key={rel.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{rel.parent_block_id} contains {rel.child_block_id}</div>
                <div className="text-xs text-muted">{rel.relation_type}</div>
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Linked external sources</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.artifact_links || []).length ? (
              data.artifact_links.map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.internal_object_label || "Block"} <span className="text-muted">â†’</span> {link.external_artifact_name}</div>
                  <div className="text-xs text-muted">{link.relation_type} Â· {link.external_artifact_version_label || "unpinned"} Â· {link.connector_name || "no connector"}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No external sources linked yet.</div>
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add linked external source</div>
              <ArtifactLinkForm
                projectId={data.block.project_id}
                internalObjectType="block"
                internalObjectId={data.block.id}
                internalObjectLabel={`${data.block.key} - ${data.block.name}`}
                artifacts={artifacts}
              />
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Traceability and history</div></CardHeader>
        <CardBody className="space-y-3">
          {(data.links || []).map((link: any) => <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="text-xs text-muted">{link.relation_type}</div></div>)}
          {(data.history || []).map((entry: any) => <div key={entry.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">Version {entry.version}</div><div className="text-xs text-muted">{entry.change_summary || entry.changed_at}</div></div>)}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}




