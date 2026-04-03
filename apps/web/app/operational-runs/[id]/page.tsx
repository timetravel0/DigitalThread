import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function OperationalRunPage({ params }: { params: { id: string } }) {
  const data = await api.operationalRun(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Operational run not found.</div>;

  const telemetry = JSON.stringify(data.operational_run.telemetry_json || {}, null, 2);
  const linkedRequirements = (data.links || []).filter((link: any) => link.relation_type === "reports_on" && (link.source_type === "operational_run" || link.target_type === "operational_run"));

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${data.operational_run.key} - Operational evidence batch`}
        description={data.operational_run.notes || data.operational_run.location}
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="font-semibold">Operational run record</div>
              <Badge tone={runTone(data.operational_run.outcome)}>{data.operational_run.outcome}</Badge>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            <Row label="Date" value={data.operational_run.date} />
            <Row label="Drone serial" value={data.operational_run.drone_serial} />
            <Row label="Location" value={data.operational_run.location} />
            <Row label="Duration" value={`${data.operational_run.duration_minutes} min`} />
            <Row label="Max temperature" value={data.operational_run.max_temperature_c ?? "n/a"} />
            <Row label="Battery consumption" value={data.operational_run.battery_consumption_pct ?? "n/a"} />
            <Row label="Outcome" value={<Badge tone={runTone(data.operational_run.outcome)}>{data.operational_run.outcome}</Badge>} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Linked requirements</div></CardHeader>
          <CardBody className="space-y-3">
            {linkedRequirements.length ? (
              linkedRequirements.map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.target_label || link.source_label || "Requirement"}</div>
                  <div className="text-xs text-muted">{link.relation_type}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No requirements linked yet.</div>
            )}
          </CardBody>
        </Card>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Telemetry</div></CardHeader>
          <CardBody>
            <pre className="overflow-auto rounded-xl border border-line bg-panel2 p-4 text-xs text-muted">{telemetry}</pre>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Impact preview</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.impact.direct || []).length ? (
              (data.impact.direct || []).map((item: any) => (
                <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-muted">{item.object_type}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No directly impacted objects found.</div>
            )}
          </CardBody>
        </Card>
      </div>
      <Link href={`/projects/${data.operational_run.project_id}/runs`} className="text-sm text-accent">
        Back to operational runs
      </Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}

function runTone(outcome: string) {
  if (outcome === "success") return "success";
  if (outcome === "degraded") return "warning";
  if (outcome === "failure") return "danger";
  return "neutral";
}
