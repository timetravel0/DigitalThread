import Link from "next/link";
import { api } from "@/lib/api-client";
import { ArtifactLinkForm } from "@/components/artifact-link-form";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { SimulationEvidenceMetadata } from "@/components/simulation-evidence-metadata";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { WorkflowActions } from "@/components/workflow-actions";

export const dynamic = "force-dynamic";

export default async function RequirementPage({ params }: { params: { id: string } }) {
  const data = await api.requirement(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Requirement not found.</div>;
  const artifacts = await api.externalArtifacts(data.requirement.project_id).catch(() => []);

  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.requirement.key} - ${data.requirement.title}`} description={data.requirement.description} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="font-semibold">Requirement record</div>
              <div className="flex flex-wrap gap-2">
                {data.requirement.status === "approved" || data.requirement.status === "in_review" ? null : (
                  <Button href={`/requirements/${data.requirement.id}/edit`} variant="secondary">Edit</Button>
                )}
                <WorkflowActions kind="requirement" id={data.requirement.id} status={data.requirement.status} />
              </div>
            </div>
          </CardHeader>
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

      {data.requirement.status === "approved" ? (
        <Card>
          <CardHeader><div className="font-semibold">Approved item editing</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This requirement is approved and cannot be edited in place.</p>
            <p>Create a new draft version to change it while keeping the approved revision intact.</p>
            <WorkflowActions kind="requirement" id={data.requirement.id} status={data.requirement.status} />
          </CardBody>
        </Card>
      ) : null}

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
          <CardHeader><div className="font-semibold">Linked external sources</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.artifact_links || []).length ? (
              data.artifact_links.map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.internal_object_label || "Requirement"} <span className="text-muted">→</span> {link.external_artifact_name}</div>
                  <div className="text-xs text-muted">{link.relation_type} · {link.external_artifact_version_label || "unpinned"} · {link.connector_name || "no connector"}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No external sources linked yet.</div>
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add linked external source</div>
              <ArtifactLinkForm
                projectId={data.requirement.project_id}
                internalObjectType="requirement"
                internalObjectId={data.requirement.id}
                internalObjectLabel={`${data.requirement.key} - ${data.requirement.title}`}
                artifacts={artifacts}
              />
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Verification evidence</div></CardHeader>
          <CardBody className="space-y-4">
            <Row label="Verification status" value={<Badge tone={verificationTone(data.verification_evaluation.status)}>{data.verification_evaluation.status}</Badge>} />
            <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
              <div className="font-medium text-text">Engine result</div>
              <div className="mt-1">
                {data.verification_evaluation.reasons.length ? data.verification_evaluation.reasons.join(" ") : "No verification notes available."}
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-line px-2 py-1">Evidence: {data.verification_evaluation.linked_evidence_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Operational batches: {data.verification_evaluation.linked_operational_run_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Tests: {data.verification_evaluation.linked_test_case_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Passed: {data.verification_evaluation.passed_test_case_count}</span>
              </div>
              {data.verification_evaluation.linked_operational_run_count ? (
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <span className="rounded-full border border-line px-2 py-1">Successful runs: {data.verification_evaluation.successful_operational_run_count}</span>
                  <span className="rounded-full border border-line px-2 py-1">Degraded runs: {data.verification_evaluation.degraded_operational_run_count}</span>
                  <span className="rounded-full border border-line px-2 py-1">Failed runs: {data.verification_evaluation.failed_operational_run_count}</span>
                </div>
              ) : null}
            </div>
            {data.verification_evidence?.length ? (
              <div className="space-y-3">
                {data.verification_evidence.map((evidence: any) => (
                  <div key={evidence.id} className="rounded-xl border border-line bg-panel2 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="font-medium">{evidence.title}</div>
                        <div className="mt-1 text-xs text-muted">{evidence.evidence_type} · {evidence.observed_at || "no observed date"}</div>
                      </div>
                      <Badge tone="accent">{evidence.evidence_type}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-muted">{evidence.summary || "No summary provided."}</div>
                    <div className="mt-2 text-xs text-muted">
                      {evidence.source_name ? <span>{evidence.source_name}</span> : <span>No source name</span>}
                      {evidence.source_reference ? <span> · {evidence.source_reference}</span> : null}
                    </div>
                    <SimulationEvidenceMetadata metadataJson={evidence.metadata_json} />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted">No verification evidence linked yet.</div>
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add verification evidence</div>
              <VerificationEvidenceForm
                projectId={data.requirement.project_id}
                subjectType="requirement"
                subjectId={data.requirement.id}
                subjectLabel={`${data.requirement.key} - ${data.requirement.title}`}
              />
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Impact objects</div></CardHeader>
        <CardBody className="space-y-3">
          {(data.impact.direct || []).map((item: any) => <ImpactItem key={item.object_id} item={item} />)}
          {(data.impact.secondary || []).map((item: any) => <ImpactItem key={item.object_id} item={item} />)}
        </CardBody>
      </Card>

      <Card>
        <CardHeader><div className="font-semibold">History</div></CardHeader>
        <CardBody className="space-y-3">
          {(data.history || []).map((entry: any) => (
            <div key={entry.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="font-medium">Version {entry.version}</div>
              <div className="text-xs text-muted">{entry.change_summary || entry.changed_at}</div>
            </div>
          ))}
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

function ImpactItem({ item }: { item: any }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="font-medium">{item.label}</div>
      <div className="text-xs text-muted">{item.object_type}</div>
    </div>
  );
}

function verificationTone(status: string) {
  if (status === "verified") return "success";
  if (status === "failed" || status === "not_covered") return "danger";
  if (status === "at_risk" || status === "partially_verified") return "warning";
  return "neutral";
}
