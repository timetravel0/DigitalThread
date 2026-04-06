import Link from "next/link";
import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import { ArtifactLinkForm } from "@/components/artifact-link-form";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { RelationshipLinkForm } from "@/components/relationship-link-form";
import { RelationshipDeleteButton } from "@/components/relationship-delete-button";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";
import { SimulationEvidenceForm } from "@/components/simulation-evidence-form";
import { SimulationEvidenceMetadata } from "@/components/simulation-evidence-metadata";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { WorkflowActions } from "@/components/workflow-actions";

export const dynamic = "force-dynamic";

export default async function TestCasePage({ params }: { params: { id: string } }) {
  const data = await api.testCase(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Test case not found.</div>;
  const project = await api.project(data.test_case.project_id).catch(() => null);
  const labels = getLabels(project?.domain_profile);
  const [artifacts, fmiContracts, requirements, blocks] = await Promise.all([
    api.externalArtifacts(data.test_case.project_id).catch(() => []),
    api.fmiContracts(data.test_case.project_id).catch(() => []),
    api.requirements(data.test_case.project_id).catch(() => []),
    api.blocks(data.test_case.project_id).catch(() => []),
  ]);
  const sysmlRelations = await api.sysmlRelations(data.test_case.project_id, { object_type: "test_case", object_id: data.test_case.id }).catch(() => []);
  const requirementLabels = new Map(requirements.map((item: any) => [item.id, `${item.key} - ${item.title}`]));
  const blockLabels = new Map(blocks.map((item: any) => [item.id, `${item.key} - ${item.name}`]));

  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.test_case.key} - ${data.test_case.title}`} description={data.test_case.description} />
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div className="font-semibold">{labels.testCase} record</div>
            <div className="flex flex-wrap gap-2">
              {data.test_case.status === "approved" || data.test_case.status === "in_review" ? null : (
                <Button href={`/test-cases/${data.test_case.id}/edit`} variant="secondary">Edit</Button>
              )}
              <WorkflowActions kind="test_case" id={data.test_case.id} status={data.test_case.status} />
            </div>
          </div>
        </CardHeader>
        <CardBody className="space-y-3">
          <Row label="Method" value={data.test_case.method} />
          <Row label="Status" value={<Badge>{data.test_case.status}</Badge>} />
          <Row label="Version" value={data.test_case.version} />
        </CardBody>
      </Card>
      {data.test_case.status === "approved" ? (
        <Card>
          <CardHeader><div className="font-semibold">Approved item editing</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This {labels.testCase.toLowerCase()} is approved and cannot be edited in place.</p>
            <p>Create a new draft version before changing the {labels.testCase.toLowerCase()} content.</p>
            <WorkflowActions kind="test_case" id={data.test_case.id} status={data.test_case.status} />
          </CardBody>
        </Card>
      ) : null}

      <Card>
        <CardHeader><div className="font-semibold">Connect this test case</div></CardHeader>
        <CardBody className="grid gap-6 xl:grid-cols-2">
          <div id="connect-requirements">
            <RelationshipLinkForm
              projectId={data.test_case.project_id}
              kind="sysml"
              sourceType="test_case"
              sourceId={data.test_case.id}
              sourceLabel={`${data.test_case.key} - ${data.test_case.title}`}
              relationType="verify"
              relationLabel="Verify requirement"
              targetType="requirement"
              targetLabel="requirement"
              targets={requirements.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.title}` }))}
              title="Requirements"
              description="Use this when the test case verifies a requirement."
              emptyDescription="Requirements belong here when this test case exists to prove them."
              submitLabel="Link requirement"
              emptyAction={<Button href={`/projects/${data.test_case.project_id}/requirements`} variant="secondary">Open requirements</Button>}
            />
          </div>
          <div id="connect-blocks">
            <RelationshipLinkForm
              projectId={data.test_case.project_id}
              kind="sysml"
              sourceType="test_case"
              sourceId={data.test_case.id}
              sourceLabel={`${data.test_case.key} - ${data.test_case.title}`}
              relationType="trace"
              relationLabel="Trace to block"
              targetType="block"
              targetLabel="block"
              targets={blocks.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.name}` }))}
              title="Blocks and realizations"
              description="Use this when the test case exercises a block directly."
              emptyDescription="Blocks belong here when the test case needs an explicit structural target."
              submitLabel="Link block"
              emptyAction={<Button href={`/projects/${data.test_case.project_id}/blocks`} variant="secondary">Open blocks</Button>}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><div className="font-semibold">SysML relations</div></CardHeader>
        <CardBody className="space-y-3">
          {sysmlRelations.length ? (
            sysmlRelations.map((relation: any) => {
              const sourceLabel = relation.source_type === "test_case" && relation.source_id === data.test_case.id
                ? `${data.test_case.key} - ${data.test_case.title}`
                : relation.source_type === "requirement"
                  ? requirementLabels.get(relation.source_id) || relation.source_type
                  : relation.source_type === "block"
                    ? blockLabels.get(relation.source_id) || relation.source_type
                    : relation.source_type;
              const targetLabel = relation.target_type === "test_case" && relation.target_id === data.test_case.id
                ? `${data.test_case.key} - ${data.test_case.title}`
                : relation.target_type === "requirement"
                  ? requirementLabels.get(relation.target_id) || relation.target_type
                  : relation.target_type === "block"
                    ? blockLabels.get(relation.target_id) || relation.target_type
                    : relation.target_type;
              return (
                <div key={relation.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium">{sourceLabel} <span className="text-muted">-&gt;</span> {targetLabel}</div>
                      <div className="text-xs text-muted">{relation.relation_type}{relation.rationale ? ` · ${relation.rationale}` : ""}</div>
                    </div>
                    <RelationshipDeleteButton kind="sysml" id={relation.id} label={`${sourceLabel} to ${targetLabel}`} />
                  </div>
                </div>
              );
            })
          ) : (
            <EmptyState
              title="No SysML relations yet"
              description="SysML relations belong here when this test case is connected to requirements or blocks. Use the link forms above to create the first one."
              action={<Button href="#connect-requirements" variant="secondary">Connect objects</Button>}
            />
          )}
        </CardBody>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Runs</div></CardHeader>
          <CardBody className="space-y-3">
            {data.runs.length ? (
              data.runs.map((run: any) => (
                <div key={run.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="flex items-center justify-between gap-4">
                    <div className="font-medium">{run.summary}</div>
                    <Badge tone={run.result === "failed" ? "danger" : run.result === "passed" ? "success" : "warning"}>{run.result}</Badge>
                  </div>
                  <div className="mt-1 text-xs text-muted">{run.execution_date}</div>
                </div>
              ))
            ) : (
              <EmptyState
                title="No runs recorded yet"
                description="Runs belong here when this test or check has actually been executed. Use the validation cockpit to capture the first result so the test case can show what was exercised in practice."
                action={<Button href={`/projects/${data.test_case.project_id}/validation`} variant="secondary">Open validation cockpit</Button>}
              />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">{labels.verificationEvidence}</div></CardHeader>
          <CardBody className="space-y-4">
            {data.verification_evidence?.length ? (
              <div className="space-y-3">
                {data.verification_evidence.map((evidence: any) => (
                  <div key={evidence.id} className="rounded-xl border border-line bg-panel2 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="font-medium">{evidence.title}</div>
                        <div className="mt-1 text-xs text-muted">{evidence.evidence_type} Â· {evidence.observed_at || "no observed date"}</div>
                      </div>
                      <Badge tone="accent">{evidence.evidence_type}</Badge>
                    </div>
                    <div className="mt-2 text-sm text-muted">{evidence.summary || "No summary provided."}</div>
                    <div className="mt-2 text-xs text-muted">
                      {evidence.source_name ? <span>{evidence.source_name}</span> : <span>No source name</span>}
                      {evidence.source_reference ? <span> Â· {evidence.source_reference}</span> : null}
                    </div>
                    <SimulationEvidenceMetadata metadataJson={evidence.metadata_json} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title={`No ${labels.verificationEvidence.toLowerCase()} linked yet`}
                description="Verification evidence belongs here when a test run, inspection, or review proves the test case. Add evidence so the verification trail stays visible."
              />
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add {labels.verificationEvidence}</div>
              <VerificationEvidenceForm
                projectId={data.test_case.project_id}
                subjectType="test_case"
                subjectId={data.test_case.id}
                subjectLabel={`${data.test_case.key} - ${data.test_case.title}`}
              />
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">{labels.simulationEvidence}</div></CardHeader>
          <CardBody className="space-y-4">
            {data.simulation_evidence?.length ? (
              <div className="space-y-4">
                {data.simulation_evidence.map((evidence: any) => (
                  <SimulationEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
                ))}
              </div>
            ) : (
              <EmptyState
                title={`No ${labels.simulationEvidence.toLowerCase()} linked yet`}
                description="Simulation evidence belongs here when a scenario or model explains the test case. Add it to connect simulation results back to the verification thread."
              />
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add {labels.simulationEvidence}</div>
              <SimulationEvidenceForm
              projectId={data.test_case.project_id}
              linkedTestCaseIds={[data.test_case.id]}
              verificationEvidenceOptions={(data.verification_evidence || []).map((item: any) => ({ id: item.id, label: item.title }))}
              fmiContractOptions={fmiContracts.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.name}` }))}
              lockedSubjectLabel={`${data.test_case.key} - ${data.test_case.title}`}
            />
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Linked external sources</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.artifact_links || []).length ? (
              data.artifact_links.map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.internal_object_label || "Test case"} <span className="text-muted">â†’</span> {link.external_artifact_name}</div>
                  <div className="text-xs text-muted">{link.relation_type} Â· {link.external_artifact_version_label || "unpinned"} Â· {link.connector_name || "no connector"}</div>
                </div>
              ))
            ) : (
              <EmptyState
                title="No external source linked"
                description="External sources belong here when a test case depends on a requirements document, design file, or other owning system. Link them to keep the source of truth explicit."
              />
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add linked external source</div>
              <ArtifactLinkForm
                projectId={data.test_case.project_id}
                internalObjectType="test_case"
                internalObjectId={data.test_case.id}
                internalObjectLabel={`${data.test_case.key} - ${data.test_case.title}`}
                artifacts={artifacts}
              />
            </div>
          </CardBody>
        </Card>
      </div>
      <Card>
          <CardHeader><div className="font-semibold">Traceability</div></CardHeader>
          <CardBody className="space-y-3">
          {data.links.map((link: any) => (
            <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div>
                  <div className="text-xs text-muted">{link.relation_type}</div>
                </div>
                <RelationshipDeleteButton kind="link" id={link.id} label={`${link.source_label || link.source_type} to ${link.target_label || link.target_type}`} />
              </div>
            </div>
          ))}
          {!data.links.length ? <EmptyState title="No traceability links yet" description="Traceability belongs here when the test case is connected to the requirements or blocks it proves. Use the link forms above to create the first relationship." action={<Button href="#connect-requirements" variant="secondary">Connect objects</Button>} /> : null}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">History</div></CardHeader>
        <CardBody className="space-y-3">
          {(data.history || []).map((entry: any) => <div key={entry.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">Version {entry.version}</div><div className="text-xs text-muted">{entry.change_summary || entry.changed_at}</div></div>)}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  return null;
}




