import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { OperationalEvidenceCard } from "@/components/operational-evidence-card";
import { OperationalEvidenceForm } from "@/components/operational-evidence-form";
import { SimulationEvidenceMetadata } from "@/components/simulation-evidence-metadata";

export const dynamic = "force-dynamic";

export default async function VerificationEvidencePage({ params }: { params: { id: string } }) {
  const data = await api.verificationEvidenceDetail(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Verification evidence not found.</div>;
  const simulationEvidence = await api.simulationEvidence(data.project_id, { internal_object_type: "verification_evidence", internal_object_id: data.id }).catch(() => []);
  const operationalEvidence = await api.operationalEvidence(data.project_id, { internal_object_type: "verification_evidence", internal_object_id: data.id }).catch(() => []);

  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.title}
        description="Verification evidence remains the generic evidence record. Simulation evidence can reference it, but does not replace it."
        action={<Link href={`/projects/${data.project_id}/requirements`} className="rounded-full border border-line px-3 py-1.5 text-sm text-text hover:bg-white/5">Back to project</Link>}
      />
      <Card>
        <CardHeader><div className="font-semibold">Verification evidence record</div></CardHeader>
        <CardBody className="space-y-3">
          <Row label="Type" value={<Badge tone="accent">{data.evidence_type}</Badge>} />
          <Row label="Observed at" value={data.observed_at || "Not recorded"} />
          <Row label="Source name" value={data.source_name || "Not recorded"} />
          <Row label="Source reference" value={data.source_reference || "Not recorded"} />
          <Row label="Summary" value={data.summary || "No summary provided"} />
          <SimulationEvidenceMetadata metadataJson={data.metadata_json} />
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Related objects</div></CardHeader>
        <CardBody className="space-y-3">
          {data.linked_objects?.length ? data.linked_objects.map((object) => {
            const href = objectHref(object.object_type, object.object_id);
            return (
              <div key={`${object.object_type}-${object.object_id}`} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{object.label}</div>
                    <div className="text-xs text-muted">{object.object_type}</div>
                  </div>
                  {href ? <Badge tone="accent"><Link href={href}>Open</Link></Badge> : <Badge>{object.object_type}</Badge>}
                </div>
              </div>
            );
          }) : <div className="text-sm text-muted">No linked objects recorded yet.</div>}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Simulation evidence linked to this record</div></CardHeader>
        <CardBody className="space-y-3">
          {simulationEvidence.length ? simulationEvidence.map((evidence: any) => (
            <div key={evidence.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-medium"><Link href={`/simulation-evidence/${evidence.id}`}>{evidence.title}</Link></div>
                  <div className="text-xs text-muted">{evidence.model_reference} · {evidence.scenario_name}</div>
                </div>
                <Badge tone={tone(evidence.result)}>{evidence.result}</Badge>
              </div>
            </div>
          )) : <div className="text-sm text-muted">No simulation evidence linked to this verification record.</div>}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Operational evidence linked to this record</div></CardHeader>
        <CardBody className="space-y-4">
          {operationalEvidence.length ? (
            <div className="space-y-4">
              {operationalEvidence.map((evidence: any) => (
                <OperationalEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted">No operational evidence linked to this verification record.</div>
          )}
          <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
            <div className="mb-3 text-sm font-medium">Add operational evidence</div>
            <OperationalEvidenceForm
              projectId={data.project_id}
              linkedVerificationEvidenceIds={[data.id]}
              lockedSubjectLabel={data.title}
            />
          </div>
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

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  return null;
}

function tone(result: string) {
  if (result === "passed") return "success";
  if (result === "failed") return "danger";
  return "warning";
}
