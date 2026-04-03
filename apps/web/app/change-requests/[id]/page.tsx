import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function ChangeRequestPage({ params }: { params: { id: string } }) {
  const data = await api.changeRequest(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Change request not found.</div>;
  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.change_request.key} - ${data.change_request.title}`} description={data.change_request.description} />
      <Card>
        <CardHeader><div className="font-semibold">Change request</div></CardHeader>
        <CardBody className="space-y-3">
          <Row label="Status" value={<Badge>{data.change_request.status}</Badge>} />
          <Row label="Severity" value={<Badge tone={data.change_request.severity === "critical" ? "danger" : data.change_request.severity === "high" ? "warning" : "neutral"}>{data.change_request.severity}</Badge>} />
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Impacted objects</div></CardHeader>
        <CardBody className="space-y-3">
          {data.impacts.map((impact: any) => <div key={impact.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{impact.object_type}</div><div className="text-xs text-muted">{impact.impact_level} - {impact.notes}</div></div>)}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Impact summary</div></CardHeader>
        <CardBody className="space-y-3">
          {data.impact_summary.map((item: any) => <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{item.label}</div><div className="text-xs text-muted">{item.object_type}</div></div>)}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}


