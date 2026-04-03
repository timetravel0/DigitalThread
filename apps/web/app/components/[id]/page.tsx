import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function ComponentPage({ params }: { params: { id: string } }) {
  const data = await api.component(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Component not found.</div>;
  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.component.key} - ${data.component.name}`} description={data.component.description} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">Component record</div></CardHeader>
          <CardBody className="space-y-3">
            <Row label="Type" value={data.component.type} />
            <Row label="Part number" value={data.component.part_number || "-"} />
            <Row label="Supplier" value={data.component.supplier || "-"} />
            <Row label="Status" value={<Badge>{data.component.status}</Badge>} />
            <Row label="Version" value={data.component.version} />
            <Row label="Metadata" value={<pre className="max-w-[320px] whitespace-pre-wrap text-right text-xs text-muted">{JSON.stringify(data.component.metadata_json, null, 2)}</pre>} />
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
      <Card>
        <CardHeader><div className="font-semibold">Traceability and change impacts</div></CardHeader>
        <CardBody className="space-y-3">
          {data.links.map((link: any) => <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="text-xs text-muted">{link.relation_type}</div></div>)}
          {data.change_impacts.map((impact: any) => <div key={impact.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{impact.impact_level} impact</div><div className="text-xs text-muted">{impact.notes}</div></div>)}
        </CardBody>
      </Card>
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


