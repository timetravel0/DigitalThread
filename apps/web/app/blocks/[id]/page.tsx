import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

export const dynamic = "force-dynamic";

export default async function BlockPage({ params }: { params: { id: string } }) {
  const data = await api.block(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Block not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.block.key} - ${data.block.name}`} description={data.block.description} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="font-semibold">Block (SysML-inspired structural element)</div>
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
            <Row label="Abstraction" value={data.block.abstraction_level} />
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

      {data.block.status === "approved" ? (
        <Card>
          <CardHeader><div className="font-semibold">Approved item editing</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This block is approved and cannot be edited in place.</p>
            <p>Create a draft version to continue modeling the block without losing history.</p>
            <WorkflowActions kind="block" id={data.block.id} status={data.block.status} />
          </CardBody>
        </Card>
      ) : null}

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
