import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function RequirementPage({ params }: { params: { id: string } }) {
  const data = await api.requirement(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Requirement not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.requirement.key} - ${data.requirement.title}`} description={data.requirement.description} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">Requirement record</div></CardHeader>
          <CardBody className="space-y-3">
            <Row label="Category" value={data.requirement.category} />
            <Row label="Priority" value={data.requirement.priority} />
            <Row label="Verification" value={data.requirement.verification_method} />
            <Row label="Status" value={<Badge>{data.requirement.status}</Badge>} />
            <Row label="Version" value={data.requirement.version} />
            <Row label="Parent" value={data.requirement.parent_requirement_id || "None"} />
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

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Traceability</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.links || []).map((link: any) => (
              <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div>
                <div className="text-xs text-muted">{link.relation_type}</div>
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Impact objects</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.impact.direct || []).map((item: any) => <ImpactItem key={item.object_id} item={item} />)}
            {(data.impact.secondary || []).map((item: any) => <ImpactItem key={item.object_id} item={item} />)}
          </CardBody>
        </Card>
      </div>

      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3">
      <div className="text-sm text-muted">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

function ImpactItem({ item }: { item: any }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="font-medium">{item.label}</div>
      <div className="text-xs text-muted">{item.object_type}</div>
    </div>
  );
}


