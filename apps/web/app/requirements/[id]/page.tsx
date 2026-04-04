import Link from "next/link";
import { api } from "@/lib/api-client";
import { ArtifactLinkForm } from "@/components/artifact-link-form";
import { ImpactVisualization, type ImpactVisualizationNode, type ImpactVisualizationSection } from "@/components/impact-visualization";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { OperationalEvidenceCard } from "@/components/operational-evidence-card";
import { OperationalEvidenceForm } from "@/components/operational-evidence-form";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";
import { SimulationEvidenceForm } from "@/components/simulation-evidence-form";
import { SimulationEvidenceMetadata } from "@/components/simulation-evidence-metadata";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { WorkflowActions } from "@/components/workflow-actions";

export const dynamic = "force-dynamic";

export default async function RequirementPage({ params }: { params: { id: string } }) {
  const data = await api.requirement(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Requirement not found.</div>;
  const [artifacts, fmiContracts] = await Promise.all([
    api.externalArtifacts(data.requirement.project_id).catch(() => []),
    api.fmiContracts(data.requirement.project_id).catch(() => []),
  ]);
  const impactSections = [
    {
      title: "Direct impacts",
      description: "Objects immediately connected to the requirement.",
      tone: "accent",
      items: (data.impact.direct || []).map((item: any) => impactNode(item, objectHref)),
      emptyText: "No direct impacts detected yet.",
    },
    {
      title: "Secondary impacts",
      description: "Objects reached through the next hop in the impact traversal.",
      tone: "warning",
      items: (data.impact.secondary || []).map((item: any) => impactNode(item, objectHref)),
      emptyText: "No secondary impacts detected yet.",
    },
    {
      title: "Related baselines",
      description: "Approved snapshots that include this requirement or its dependencies.",
      tone: "neutral",
      items: (data.impact.related_baselines || []).map((item: any) => ({
        label: item.name,
        objectType: "baseline",
        href: `/baselines/${item.id}`,
        meta: `${item.status} snapshot`,
      })),
      emptyText: "No related baselines found.",
    },
    {
      title: "Open change requests",
      description: "Active change records that may affect this requirement.",
      tone: "danger",
      items: (data.impact.open_change_requests || []).map((item: any) => ({
        label: `${item.key} - ${item.title}`,
        objectType: "change_request",
        href: `/change-requests/${item.id}`,
        meta: `${item.status} · ${item.severity}`,
      })),
      emptyText: "No open change requests found.",
    },
  ] satisfies ImpactVisualizationSection[];

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
            <Row label="Approval status" value={<Badge tone={approvalTone(data.requirement.status)}>{data.requirement.status}</Badge>} />
            <Row label="Version" value={data.requirement.version} />
            <Row label="Parent" value={data.requirement.parent_requirement_id || "None"} />
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-xs text-muted">
              This is the authored lifecycle state. The computed verification status is shown separately below.
            </div>
          </CardBody>
        </Card>
        <ImpactVisualization
          title="Impact map"
          description="A compact view of objects affected by this requirement and the review records that stay linked to it."
          root={{
            eyebrow: "Requirement root",
            label: `${data.requirement.key} - ${data.requirement.title}`,
            description: data.requirement.description || "No description provided.",
            badges: [
              { label: `Approval: ${data.requirement.status}`, tone: approvalTone(data.requirement.status) as "neutral" | "success" | "warning" | "danger" | "accent" },
              { label: `Verification: ${humanizeStatus(data.verification_evaluation.status)}`, tone: verificationTone(data.verification_evaluation.status) as "neutral" | "success" | "warning" | "danger" | "accent" },
            ],
          }}
          sections={impactSections}
        />
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
            <Row label="Verification status" value={<Badge tone={verificationTone(data.verification_evaluation.status)}>{humanizeStatus(data.verification_evaluation.status)}</Badge>} />
            <div className="rounded-2xl border border-line bg-panel2 p-4 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-muted">Why this status?</div>
                  <div className="mt-1 text-sm font-medium text-text">A reviewer-friendly explanation of the computed result.</div>
                </div>
                <Badge tone={verificationTone(data.verification_evaluation.status)}>{humanizeStatus(data.verification_evaluation.status)}</Badge>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <Info label="Decision source" value={humanizeDecisionSource(data.verification_evaluation.decision_source)} />
                <Info label="Plain-language summary" value={data.verification_evaluation.decision_summary || "No summary available."} />
              </div>
              <div className="rounded-xl border border-dashed border-line bg-panel p-3">
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Main reasons</div>
                {data.verification_evaluation.reasons.length ? (
                  <ul className="mt-2 space-y-1 text-sm text-text">
                    {data.verification_evaluation.reasons.map((reason: string) => <li key={reason} className="flex gap-2"><span className="mt-1 h-1.5 w-1.5 rounded-full bg-accent" />{reason}</li>)}
                  </ul>
                ) : (
                  <div className="mt-2 text-sm text-muted">No verification notes available.</div>
                )}
              </div>
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-line px-2 py-1">Evidence: {data.verification_evaluation.linked_evidence_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Operational batches: {data.verification_evaluation.linked_operational_run_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Tests: {data.verification_evaluation.linked_test_case_count}</span>
                <span className="rounded-full border border-line px-2 py-1">Passed: {data.verification_evaluation.passed_test_case_count}</span>
              </div>
              {data.verification_evaluation.linked_operational_run_count ? (
                <div className="flex flex-wrap gap-2 text-xs">
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
                        <div className="mt-1 text-xs text-muted">Captured {evidence.observed_at || "no observed date"} · {evidence.evidence_type}</div>
                      </div>
                      <Badge tone="accent">{evidence.evidence_type}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-muted">{evidence.summary || "No summary provided."}</div>
                    <div className="mt-3 grid gap-2 text-xs text-muted md:grid-cols-3">
                      <div><span className="text-text">Source system:</span> {evidence.source_name || "Not recorded"}</div>
                      <div><span className="text-text">Source reference:</span> {evidence.source_reference || "Not recorded"}</div>
                      <div><span className="text-text">Evidence type:</span> {evidence.evidence_type}</div>
                    </div>
                    {evidence.linked_objects?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {evidence.linked_objects.map((object: any) => {
                          const href = objectHref(object.object_type, object.object_id);
                          const chip = (
                            <span className="rounded-full border border-line bg-white/5 px-2 py-1 text-xs text-text">
                              {object.label}
                            </span>
                          );
                          return href ? <Link key={object.object_id} href={href}>{chip}</Link> : <span key={object.object_id}>{chip}</span>;
                        })}
                      </div>
                    ) : null}
                    <SimulationEvidenceMetadata metadataJson={evidence.metadata_json} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No verification evidence linked yet"
                description="Add evidence manually, or link this requirement to existing test or operational sources first. The computed verification status will remain not covered until evidence is linked."
                action={<Button href="#add-verification-evidence" variant="secondary">Open evidence form</Button>}
              />
            )}
            <div id="add-verification-evidence" className="rounded-xl border border-dashed border-line bg-panel2 p-4">
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
        <CardHeader><div className="font-semibold">Simulation evidence</div></CardHeader>
        <CardBody className="space-y-4">
          {data.simulation_evidence?.length ? (
            <div className="space-y-4">
              {data.simulation_evidence.map((evidence: any) => (
                <SimulationEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No simulation evidence linked yet"
              description="Capture simulation evidence when the requirement is assessed with a model or scenario. Link it to the requirement, related tests, or supporting verification evidence."
              action={<Button href="#add-simulation-evidence" variant="secondary">Open simulation evidence form</Button>}
            />
          )}
          <div id="add-simulation-evidence" className="rounded-xl border border-dashed border-line bg-panel2 p-4">
            <div className="mb-3 text-sm font-medium">Add simulation evidence</div>
            <SimulationEvidenceForm
              projectId={data.requirement.project_id}
              linkedRequirementIds={[data.requirement.id]}
              verificationEvidenceOptions={(data.verification_evidence || []).map((item: any) => ({ id: item.id, label: item.title }))}
              fmiContractOptions={fmiContracts.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.name}` }))}
              lockedSubjectLabel={`${data.requirement.key} - ${data.requirement.title}`}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><div className="font-semibold">Operational evidence</div></CardHeader>
        <CardBody className="space-y-4">
          {data.operational_evidence?.length ? (
            <div className="space-y-4">
              {data.operational_evidence.map((evidence: any) => (
                <OperationalEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="No operational evidence linked yet"
              description="Capture a field or telemetry batch when operational feedback is available. Link it to this requirement or to a supporting verification record."
              action={<Button href="#add-operational-evidence" variant="secondary">Open evidence form</Button>}
            />
          )}
          <div id="add-operational-evidence" className="rounded-xl border border-dashed border-line bg-panel2 p-4">
            <div className="mb-3 text-sm font-medium">Add operational evidence</div>
            <OperationalEvidenceForm
              projectId={data.requirement.project_id}
              linkedRequirementIds={[data.requirement.id]}
              verificationEvidenceOptions={(data.verification_evidence || []).map((item: any) => ({ id: item.id, label: item.title }))}
              lockedSubjectLabel={`${data.requirement.key} - ${data.requirement.title}`}
            />
          </div>
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

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 text-sm text-text">{value}</div>
    </div>
  );
}

function verificationTone(status: string) {
  if (status === "verified") return "success";
  if (status === "failed" || status === "not_covered") return "danger";
  if (status === "at_risk" || status === "partially_verified") return "warning";
  return "neutral";
}

function approvalTone(status: string) {
  if (status === "approved" || status === "implemented") return "success";
  if (status === "in_review") return "warning";
  if (status === "rejected" || status === "failed") return "danger";
  return "neutral";
}

function humanizeStatus(status: string) {
  return status.replaceAll("_", " ");
}

function humanizeDecisionSource(source: string) {
  if (!source) return "Not specified";
  return source.charAt(0).toUpperCase() + source.slice(1);
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "operational_run") return `/operational-runs/${objectId}`;
  if (objectType === "block") return `/blocks/${objectId}`;
  if (objectType === "component") return `/components/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "operational_evidence") return `/operational-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  return null;
}

function impactNode(item: any, hrefResolver: (objectType: string, objectId: string) => string | null): ImpactVisualizationNode {
  const href = hrefResolver(item.object_type, item.object_id);
  return {
    label: item.label,
    objectType: item.object_type,
    href,
    meta: [item.code, item.status, item.version != null ? `v${item.version}` : null].filter(Boolean).join(" · ") || null,
    tone: item.object_type === "change_request" ? "danger" : item.object_type === "baseline" ? "accent" : "neutral",
  };
}
