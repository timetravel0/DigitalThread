import Link from "next/link";
import { api } from "@/lib/api-client";
import { ImpactVisualization, type ImpactVisualizationSection } from "@/components/impact-visualization";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

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
          <Row label="Status" value={<Badge tone={statusTone(data.change_request.status)}>{data.change_request.status}</Badge>} />
          <Row label="Severity" value={<Badge tone={data.change_request.severity === "critical" ? "danger" : data.change_request.severity === "high" ? "warning" : "neutral"}>{data.change_request.severity}</Badge>} />
          <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
            <div className="mb-3 text-sm font-medium">Lifecycle action</div>
            <WorkflowActions kind="change_request" id={data.change_request.id} status={data.change_request.status} />
          </div>
        </CardBody>
      </Card>
      <ImpactVisualization
        title="Impact map"
        description="A compact view of objects affected by this change request, grouped by impact level."
        root={{
          eyebrow: "Change request root",
          label: `${data.change_request.key} - ${data.change_request.title}`,
          description: data.change_request.description || "No description provided.",
          badges: [
            { label: `Status: ${data.change_request.status}`, tone: statusTone(data.change_request.status) as "neutral" | "success" | "warning" | "danger" | "accent" },
            { label: `Severity: ${data.change_request.severity}`, tone: data.change_request.severity === "critical" ? "danger" : data.change_request.severity === "high" ? "warning" : "neutral" },
          ],
        }}
        sections={buildChangeRequestSections(data)}
      />
      <Card>
        <CardHeader><div className="font-semibold">Lifecycle history</div></CardHeader>
        <CardBody className="space-y-3">
          {data.history.length ? (
            data.history.map((event: any) => (
              <div key={event.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="font-medium">{event.from_status} → {event.to_status}</div>
                  <Badge tone={historyTone(event.to_status)}>{event.action}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted">{event.actor || "system"} · {event.created_at}</div>
                {event.comment ? <div className="mt-2 text-sm text-muted">{event.comment}</div> : null}
              </div>
            ))
          ) : (
            <div className="text-sm text-muted">No lifecycle events recorded yet.</div>
          )}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}

function statusTone(status: string) {
  if (status === "approved" || status === "implemented" || status === "closed") return "success";
  if (status === "analysis") return "warning";
  if (status === "rejected") return "danger";
  return "neutral";
}

function historyTone(status: string) {
  if (status === "approved" || status === "implemented" || status === "closed") return "success";
  if (status === "analysis") return "warning";
  if (status === "rejected") return "danger";
  return "neutral";
}

function buildChangeRequestSections(data: any): ImpactVisualizationSection[] {
  const summaryById = new Map<string, any>();
  for (const item of data.impact_summary || []) summaryById.set(item.object_id, item);
  const grouped = { high: [] as any[], medium: [] as any[], low: [] as any[] };
  for (const impact of data.impacts || []) {
    const summary = summaryById.get(impact.object_id);
    const node = {
      label: summary?.label || impact.object_type,
      objectType: summary?.object_type || impact.object_type,
      href: hrefFor(summary?.object_type || impact.object_type, impact.object_id),
      meta: `${impact.impact_level} · ${impact.notes}`,
      tone: impactLevelTone(impact.impact_level),
    };
    if (impact.impact_level === "high") grouped.high.push(node);
    else if (impact.impact_level === "medium") grouped.medium.push(node);
    else grouped.low.push(node);
  }
  return [
    {
      title: "High impact",
      description: "Objects that need immediate attention.",
      tone: "danger",
      items: grouped.high,
      emptyText: "No high impact objects linked yet.",
    },
    {
      title: "Medium impact",
      description: "Objects that should be reviewed before release.",
      tone: "warning",
      items: grouped.medium,
      emptyText: "No medium impact objects linked yet.",
    },
    {
      title: "Low impact",
      description: "Objects with a smaller expected effect.",
      tone: "accent",
      items: grouped.low,
      emptyText: "No low impact objects linked yet.",
    },
  ];
}

function impactLevelTone(level: string) {
  if (level === "high") return "danger";
  if (level === "medium") return "warning";
  return "accent";
}

function hrefFor(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "operational_run") return `/operational-runs/${objectId}`;
  if (objectType === "block") return `/blocks/${objectId}`;
  if (objectType === "component") return `/components/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "operational_evidence") return `/operational-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  if (objectType === "baseline") return `/baselines/${objectId}`;
  if (objectType === "change_request") return `/change-requests/${objectId}`;
  return null;
}
