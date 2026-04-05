import Link from "next/link";
import { api } from "@/lib/api-client";
import { getLabels } from "@/lib/labels";
import type { STEPAP242ContractResponse, SysMLMappingContractResponse } from "@/lib/types";
import { ViewCue } from "@/components/view-cue";
import { ProjectTabs } from "@/components/project-tabs";
import { TraceabilityGraph } from "@/components/traceability-graph";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { OperationalEvidenceCard } from "@/components/operational-evidence-card";
import { OperationalEvidenceForm } from "@/components/operational-evidence-form";
import { FMIContractForm } from "@/components/fmi-contract-form";
import { RelationshipRegistry } from "@/components/relationship-registry";
import { ProjectImportForm } from "@/components/project-import-form";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";
import { SimulationEvidenceForm } from "@/components/simulation-evidence-form";
import { ValidationWorkbench } from "@/components/validation-workbench";
import { VerificationStatusBreakdownCard } from "@/components/verification-status-breakdown";

export const dynamic = "force-dynamic";

type LayerFilter = "all" | "logical" | "physical";

const sysmlViews = [
  { key: "block-structure", label: "Block Structure" },
  { key: "satisfaction", label: "Satisfaction" },
  { key: "verification", label: "Verification" },
  { key: "derivations", label: "Derivations" },
  { key: "mapping-contract", label: "Mapping Contract" },
];

const layerViews: { key: LayerFilter; label: string }[] = [
  { key: "all", label: "All layers" },
  { key: "logical", label: "Logical" },
  { key: "physical", label: "Physical" },
];

type GraphFocus = "core" | "all" | "requirements" | "blocks" | "parts" | "tests" | "evidence";

function getGraphFocusViews(labels: { requirements: string; blocks: string; testCases: string }) {
  return [
    { key: "core", label: "Walk the thread" },
    { key: "requirements", label: labels.requirements },
    { key: "blocks", label: labels.blocks },
    { key: "parts", label: "Parts" },
    { key: "tests", label: labels.testCases },
    { key: "evidence", label: "Evidence" },
    { key: "all", label: "All" },
  ] as const satisfies { key: GraphFocus; label: string }[];
}

export default async function ProjectWorkspace({ params, searchParams }: { params: { id: string; section?: string[] }; searchParams?: { view?: string; focus?: string; selected?: string; kind?: string; relation?: string; evidence?: string; layer?: string } }) {
  const projectId = params.id;
  const section = params.section?.[0] ?? "";
  const view = searchParams?.view || "block-structure";
  const selectedNodeId = typeof searchParams?.selected === "string" ? searchParams.selected : null;
  const layer: LayerFilter = searchParams?.layer === "logical" || searchParams?.layer === "physical" ? searchParams.layer : "all";
  const [project, dashboard, requirements, blocks, components, tests, runs, links, baselines, nonConformities, changeRequests, reviewQueue, registrySummary, verificationEvidence, simulationEvidence, operationalEvidence, artifactLinks, sysmlRelations, fmiContracts] = await Promise.all([
    api.project(projectId).catch(() => null),
    api.projectDashboard(projectId).catch(() => null),
    api.requirements(projectId).catch(() => []),
    api.blocks(projectId).catch(() => []),
    api.components(projectId).catch(() => []),
    api.testCases(projectId).catch(() => []),
    api.operationalRuns(projectId).catch(() => []),
    api.links(projectId).catch(() => []),
    api.baselines(projectId).catch(() => []),
    api.nonConformities(projectId).catch(() => []),
    api.changeRequests(projectId).catch(() => []),
    api.reviewQueue(projectId).catch(() => null),
    api.authoritativeRegistrySummary(projectId).catch(() => null),
    api.verificationEvidence(projectId).catch(() => []),
    api.simulationEvidence(projectId).catch(() => []),
    api.operationalEvidence(projectId).catch(() => []),
    api.artifactLinks(projectId).catch(() => []),
    api.sysmlRelations(projectId).catch(() => []),
    api.fmiContracts(projectId).catch(() => []),
  ]);
  const registryLabels = buildRegistryLabels({ requirements, blocks, components, tests, runs, nonConformities, changeRequests, verificationEvidence, simulationEvidence, operationalEvidence, fmiContracts });

  if (!project) return <EmptyState title="Project not found" description="The project may have been removed or the API is not available." />;
  const labels = getLabels(project.domain_profile);
  const focusViews = getGraphFocusViews(labels);
  const focus: GraphFocus = focusViews.some((item) => item.key === searchParams?.focus) ? (searchParams?.focus as GraphFocus) : "core";

  if (section === "sysml") {
    const tree = await api.sysmlTree(project.id).catch(() => null);
    const satisfaction = await api.sysmlSatisfaction(project.id).catch(() => null);
    const verification = await api.sysmlVerification(project.id).catch(() => null);
    const derivations = await api.sysmlDerivations(project.id).catch(() => null);
    const mappingContract = await api.sysmlMappingContract(project.id).catch(() => null);
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - ${project.name}`} description="SysML-inspired practice views for blocks, satisfaction, verification, derivation, and the explicit mapping contract." />
        <ProjectTabs section={section} />
        <div className="flex flex-wrap gap-2">
          {sysmlViews.map((item) => <Button key={item.key} href={`/projects/${project.id}/sysml?view=${item.key}`} variant={view === item.key ? "primary" : "secondary"}>{item.label}</Button>)}
        </div>
        {view === "block-structure" ? (
          <div className="flex flex-wrap gap-2">
            {layerViews.map((item) => (
              <Button key={item.key} href={buildQueryHref(`/projects/${project.id}/sysml`, { view, layer: item.key })} variant={layer === item.key ? "primary" : "secondary"}>
                {item.label}
              </Button>
            ))}
          </div>
        ) : null}
        {view === "mapping-contract" ? (
          <MappingContractView contract={mappingContract} labels={labels} />
        ) : view === "satisfaction" ? (
          <Card><CardHeader><div className="font-semibold">Satisfaction</div></CardHeader><CardBody><ObjectList items={(satisfaction?.rows || []).flatMap((row) => row.requirements.map((req) => ({ label: `${row.block.key} satisfies ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : view === "verification" ? (
          <Card><CardHeader><div className="font-semibold">Verification</div></CardHeader><CardBody><ObjectList items={(verification?.rows || []).flatMap((row) => row.requirements.map((req) => ({ label: `${row.test_case.key} verifies ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : view === "derivations" ? (
          <Card><CardHeader><div className="font-semibold">Derivations</div></CardHeader><CardBody><ObjectList items={(derivations?.rows || []).flatMap((row) => row.derived_requirements.map((req) => ({ label: `${row.source_requirement.key} derived from ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : (
          <Card>
            <CardHeader><div className="font-semibold">Block structure</div></CardHeader>
            <CardBody className="space-y-3">
              <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
                The seeded drone project demonstrates the SysML <span className="text-text">contains</span> relationship with a top-level <span className="text-text">Drone System</span> block and its subsystems. Use the layer toggle to switch between logical architecture and physical realization.
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <ViewCue layer="logical" />
                <ViewCue layer="physical" />
              </div>
              <BlockTree nodes={filterBlockTree(tree?.roots || [], layer)} />
            </CardBody>
          </Card>
        )}
      </div>
    );
  }

  if (section === "step-ap242") {
    const contract = await api.stepAP242Contract(project.id).catch(() => null);
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - STEP AP242`}
          description="A lightweight AP242-style part contract derived from components, part numbers, and cad_part external artifacts."
        />
        <ProjectTabs section={section} />
        <StepAP242ContractView contract={contract} />
      </div>
    );
  }

  if (section === "graph") {
    const [tree, sysmlRelations, evidence, externalArtifacts] = await Promise.all([
      api.sysmlTree(project.id).catch(() => null),
      api.sysmlRelations(project.id).catch(() => []),
      api.verificationEvidence(project.id).catch(() => []),
      api.externalArtifacts(project.id).catch(() => []),
    ]);
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Traceability Graph`}
          description="Walk the thread from mission requirements through subsystems, software realization nodes, CAD parts, tests, and evidence."
          action={
            <div className="flex flex-wrap gap-2">
              <Button href={`/projects/${project.id}/links`} variant="secondary">{labels.links}</Button>
              <Button href={`/projects/${project.id}/matrix`} variant="secondary">Matrix view</Button>
            </div>
          }
        />
        <ProjectTabs section={section} />
        <div className="flex flex-wrap gap-2">
          {focusViews.map((item) => (
            <Button key={item.key} href={`/projects/${project.id}/graph?focus=${item.key}`} variant={focus === item.key ? "primary" : "secondary"}>
              {item.label}
            </Button>
          ))}
        </div>
        <div className="rounded-2xl border border-dashed border-line bg-panel px-4 py-3 text-sm text-muted">
          {selectedNodeId
            ? "Clicking a box opens the focused graph for that object. The view now shows only the selected object plus the boxes with direct incoming and outgoing links."
            : "The graph shows the full project network for the chosen focus. Click any box to open a focused graph with direct incoming and outgoing links."}
        </div>
        <TraceabilityGraph
          focus={focus}
          selectedNodeId={selectedNodeId}
          selectionBaseHref={`/projects/${project.id}/graph?focus=${focus}`}
          blocks={blocks}
          tree={tree?.roots || []}
          requirements={requirements}
          components={components}
          externalArtifacts={externalArtifacts}
          tests={tests}
          runs={runs}
          links={links}
          artifactLinks={artifactLinks}
          sysmlRelations={sysmlRelations}
          evidence={evidence}
        />
      </div>
    );
  }

  if (section === "review-queue") {
    return <SimpleListPage project={project} section={section} title="Review Queue" description="Items waiting in review." items={(reviewQueue?.items || []).map((item) => ({ key: item.key, label: `${item.object_type}: ${item.title}`, status: item.status, href: `/${item.object_type === "test_case" ? "test-cases" : item.object_type === "block" ? "blocks" : "requirements"}/${item.id}` }))} />;
  }

  if (section === "validation") {
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Validation`}
          description="A SidSat-style validation cockpit for non-technical reviewers. Pick a target requirement, choose a focus, and run a lightweight validation check with immediate alerts."
        />
        <ProjectTabs section={section} />
        <ValidationWorkbench
          projectCode={project.code}
          projectName={project.name}
          requirements={requirements}
        />
      </div>
    );
  }

  if (section === "requirements") return <SimpleListPage project={project} section={section} title={labels.requirements} description="Editable requirements with approval workflow." items={requirements.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/requirements/${item.id}` }))} createHref={`/requirements/new?project=${project.id}`} createLabel={`Create ${labels.requirement}`} />;
  if (section === "software") {
    const softwareComponents = components.filter((item: any) => item.type === "software_module");
    const softwareDetails = await Promise.all(softwareComponents.map((item: any) => api.component(item.id).catch(() => null)));
    const linkedRequirementCount = softwareDetails.reduce((count, detail: any) => count + (detail?.links || []).filter((link: any) => link.source_type === "requirement" || link.target_type === "requirement").length, 0);
    const linkedEvidenceCount = softwareDetails.reduce((count, detail: any) => count + (detail?.verification_evidence || []).length, 0);
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Software`}
          description="Explicit software realization traceability for flight software and other software modules."
          action={<Button href={`/components/new?project=${project.id}`} variant="secondary">Create component</Button>}
        />
        <ProjectTabs section={section} />
        <div className="grid gap-4 md:grid-cols-3">
          <Mini metric="Software modules" value={softwareComponents.length} />
          <Mini metric="Requirement links" value={linkedRequirementCount} />
          <Mini metric="Evidence records" value={linkedEvidenceCount} />
        </div>
        {softwareComponents.length ? (
          <div className="grid gap-6 xl:grid-cols-2">
            {softwareDetails.map((detail: any, index: number) => {
              if (!detail) return null;
              const metadata = detail.component.metadata_json || {};
              const repository = metadata.repository || metadata.repository_ref || "Not recorded";
              const branch = metadata.branch || metadata.ref || "Not recorded";
              const entryPoint = metadata.entry_point || metadata.main_module || "Not recorded";
              const traceLinks = (detail.links || []).filter((link: any) => {
                const relation = String(link.relation_type || "");
                return relation === "allocated_to" || relation === "uses" || relation === "satisfies" || relation === "trace";
              });
              return (
                <Card key={detail.component.id}>
                  <CardHeader>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold">{detail.component.key} - {detail.component.name}</div>
                        <div className="mt-1 text-xs text-muted">Software realization artifact</div>
                      </div>
                      <Badge tone="warning">{detail.component.status}</Badge>
                    </div>
                  </CardHeader>
                  <CardBody className="space-y-3">
                    <div className="grid gap-2 text-sm">
                      <Row label="Version" value={detail.component.version} />
                      <Row label="Repository" value={repository} />
                      <Row label="Branch" value={branch} />
                      <Row label="Entry point" value={entryPoint} />
                    </div>
                    <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">
                      This surface makes software realization explicit. {labels.requirements}, {labels.blocks}, and evidence can trace directly to the software module instead of hiding it inside a generic component list.
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs uppercase tracking-[0.2em] text-muted">Traceability</div>
                      {traceLinks.length ? (
                        <div className="space-y-2">
                          {traceLinks.map((link: any) => (
                            <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                              <div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div>
                              <div className="text-xs text-muted">{link.relation_type}{link.rationale ? ` Â· ${link.rationale}` : ""}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-muted">No requirement, block, or trace links found for this software module.</div>
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="text-xs uppercase tracking-[0.2em] text-muted">Evidence</div>
                      {detail.verification_evidence?.length ? (
                        <div className="space-y-2">
                          {detail.verification_evidence.map((evidence: any) => (
                            <div key={evidence.id} className="rounded-xl border border-line bg-panel2 p-3">
                              <div className="font-medium">{evidence.title}</div>
                              <div className="mt-1 text-xs text-muted">{evidence.evidence_type} Â· {evidence.observed_at || "no observed date"}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-sm text-muted">No verification evidence linked yet.</div>
                      )}
                    </div>
                    <Button href={`/components/${detail.component.id}`} variant="secondary">Open component detail</Button>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        ) : (
          <EmptyState title="No software modules yet" description="Create a component with type software_module to expose software realization traceability explicitly." />
        )}
      </div>
    );
  }
  if (section === "blocks") {
    const filteredBlocks = layer === "all" ? blocks : blocks.filter((item: any) => item.abstraction_level === layer);
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Blocks`}
          description={layer === "all" ? "SysML-inspired structural elements. Switch layers to focus on logical or physical blocks." : `${layer === "logical" ? "Logical architecture" : "Physical realization"} blocks only.`}
          action={<Button href={`/blocks/new?project=${project.id}`}>Create</Button>}
        />
        <ProjectTabs section={section} />
        <div className="flex flex-wrap gap-2">
          {layerViews.map((item) => (
            <Button key={item.key} href={buildQueryHref(`/projects/${project.id}/blocks`, { layer: item.key })} variant={layer === item.key ? "primary" : "secondary"}>
              {item.label}
            </Button>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <ViewCue layer="logical" />
          <ViewCue layer="physical" />
        </div>
        <Card>
          <CardHeader><div className="font-semibold">{labels.blocks}</div></CardHeader>
          <CardBody>
            {filteredBlocks.length ? (
              <div className="space-y-3">
                {filteredBlocks.map((item: any) => (
                  <Link key={item.key} href={`/blocks/${item.id}`} className={`block rounded-xl border p-4 hover:border-accent/50 ${item.abstraction_level === "physical" ? "border-amber-400/30 bg-amber-500/5" : "border-sky-400/30 bg-sky-500/5"}`}>
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{item.key} - {item.name}</div>
                        <div className="text-xs text-muted">{item.block_kind} Â· v{item.version}</div>
                      </div>
                      <Badge tone={item.abstraction_level === "physical" ? "warning" : "accent"}>{item.abstraction_level}</Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No blocks in this layer" description="Switch layers or create additional blocks to populate the view." />
            )}
          </CardBody>
        </Card>
      </div>
    );
  }
  if (section === "components") return <SimpleListPage project={project} section={section} title="Components" description="Realization objects, including software modules." items={components.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.name}`, status: item.status, href: `/components/${item.id}` }))} />;
  if (section === "tests") return <SimpleListPage project={project} section={section} title={labels.testCases} description="Verification artifacts with workflow and history." items={tests.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/test-cases/${item.id}` }))} createHref={`/test-cases/new?project=${project.id}`} createLabel={`Create ${labels.testCase}`} />;
  if (section === "runs") return <SimpleListPage project={project} section={section} title={`${labels.operationalRun}s`} description="Field evidence and telemetry." items={runs.map((run: any) => ({ key: run.key, label: `${run.key} - ${run.notes}`, status: run.outcome, href: `/operational-runs/${run.id}` }))} createHref={`/operational-runs/new?project=${project.id}`} />;
  if (section === "operational-evidence") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - ${labels.operationalEvidence}`} description="Batch-style operational feedback linked to requirements and verification evidence." />
        <ProjectTabs section={section} />
        <Card>
          <CardHeader><div className="font-semibold">{labels.operationalEvidence} batches</div></CardHeader>
          <CardBody className="space-y-4">
            {operationalEvidence.length ? (
              <div className="space-y-4">
                {operationalEvidence.map((evidence: any) => (
                  <OperationalEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
                ))}
              </div>
            ) : (
              <EmptyState title="No operational evidence yet" description="Add the first operational evidence batch to capture source, coverage window, observations, and quality status." />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Add {labels.operationalEvidence}</div></CardHeader>
          <CardBody>
            <OperationalEvidenceForm
              projectId={project.id}
              requirementOptions={requirements.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.title}` }))}
              verificationEvidenceOptions={verificationEvidence.map((item: any) => ({ id: item.id, label: item.title }))}
            />
          </CardBody>
        </Card>
      </div>
    );
  }
  if (section === "simulation-evidence") {
    const [simulationEvidence, simulationVerificationEvidence] = await Promise.all([
      api.simulationEvidence(project.id).catch(() => []),
      api.verificationEvidence(project.id).catch(() => []),
    ]);
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - ${labels.simulationEvidence}`} description="First-class simulation evidence records linked to requirements, tests, and verification evidence." />
        <ProjectTabs section={section} />
        <Card>
          <CardHeader><div className="font-semibold">{labels.simulationEvidence} records</div></CardHeader>
          <CardBody className="space-y-4">
            {simulationEvidence.length ? (
              <div className="space-y-4">
                {simulationEvidence.map((evidence: any) => (
                  <SimulationEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
                ))}
              </div>
            ) : (
              <EmptyState title="No simulation evidence yet" description="Add the first simulation evidence record to capture model, scenario, inputs, and observed behavior." />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Add {labels.simulationEvidence}</div></CardHeader>
          <CardBody>
            <SimulationEvidenceForm
              projectId={project.id}
              requirementOptions={requirements.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.title}` }))}
              testCaseOptions={tests.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.title}` }))}
              verificationEvidenceOptions={simulationVerificationEvidence.map((item: any) => ({ id: item.id, label: item.title }))}
              fmiContractOptions={fmiContracts.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.name}` }))}
            />
          </CardBody>
        </Card>
      </div>
    );
  }
  if (section === "fmi") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - FMI`} description="A lightweight placeholder contract for simulation interoperability, with explicit model reference fields." />
        <ProjectTabs section={section} />
        <Card>
          <CardHeader><div className="font-semibold">FMI placeholder contracts</div></CardHeader>
          <CardBody className="space-y-4">
            {fmiContracts.length ? (
              <div className="space-y-3">
                {fmiContracts.map((contract: any) => (
                  <Link key={contract.id} href={`/fmi-contracts/${contract.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{contract.key} - {contract.name}</div>
                        <div className="text-xs text-muted">{contract.model_identifier} Ã‚Â· {contract.contract_version}</div>
                      </div>
                      <Badge tone="accent">{contract.linked_simulation_evidence_count} simulation records</Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No FMI contracts yet" description="Create a placeholder contract to give simulation evidence an explicit model reference structure." />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Add FMI contract</div></CardHeader>
          <CardBody>
            <FMIContractForm projectId={project.id} />
          </CardBody>
        </Card>
      </div>
    );
  }
  if (section === "import") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - Import`} description="Paste JSON or CSV records to create external artifacts and verification evidence." />
        <ProjectTabs section={section} />
        <ProjectImportForm projectId={project.id} />
      </div>
    );
  }
  if (section === "links") {
    const kind = searchParams?.kind === "requirements" || searchParams?.kind === "links" || searchParams?.kind === "evidence" ? searchParams.kind : "all";
    const relation = kind === "links" && (searchParams?.relation === "generic" || searchParams?.relation === "sysml" || searchParams?.relation === "artifact") ? searchParams.relation : "all";
    const evidence = kind === "evidence" && (searchParams?.evidence === "verification" || searchParams?.evidence === "simulation" || searchParams?.evidence === "operational") ? searchParams.evidence : "all";
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Relationship Registry`}
          description="A filterable registry for requirements, links, and evidence so reviewers can inspect traceability in one place."
          action={
            <div className="flex flex-wrap gap-2">
              <Button href={`/projects/${project.id}/graph`} variant="secondary">Traceability graph</Button>
              <Button href={`/projects/${project.id}/matrix`} variant="secondary">Matrix view</Button>
            </div>
          }
        />
        <ProjectTabs section={section} />
        <RelationshipRegistry
          projectId={project.id}
          kind={kind as any}
          linkKind={relation as any}
          evidenceKind={evidence as any}
          labels={registryLabels}
          requirements={requirements}
          links={links}
          sysmlRelations={sysmlRelations}
          artifactLinks={artifactLinks}
          verificationEvidence={verificationEvidence}
          simulationEvidence={simulationEvidence}
          operationalEvidence={operationalEvidence}
        />
      </div>
    );
  }
  if (section === "baselines") return <SimpleListPage project={project} section={section} title={labels.baselines} description="Approved-only snapshots of internal state. Use configuration contexts for broader review-gate snapshots." items={baselines.map((baseline: any) => ({ key: baseline.id, label: baseline.name, status: baseline.status, href: `/baselines/${baseline.id}` }))} />;
  if (section === "non-conformities") return <SimpleListPage project={project} section={section} title={labels.nonConformities} description="First-class issue records with their own lifecycle and traceability." items={nonConformities.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/non-conformities/${item.id}` }))} />;
  if (section === "change-requests") return <SimpleListPage project={project} section={section} title={labels.changeRequests} description="Impact-driven change management." items={changeRequests.map((cr: any) => ({ key: cr.key, label: `${cr.key} - ${cr.title}`, status: cr.status, href: `/change-requests/${cr.id}` }))} />;
  if (section === "authoritative-sources") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - Authoritative Sources`} description="Federated metadata pointers, connectors, configuration contexts, and the review-gate bridge to baselines." action={<Button href={`/projects/${project.id}/authoritative-sources`}>Open registry</Button>} />
        <ProjectTabs section={section} />
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <Mini metric="Connectors" value={registrySummary?.connectors ?? 0} />
          <Mini metric="Artifacts" value={registrySummary?.external_artifacts ?? 0} />
          <Mini metric="Versions" value={registrySummary?.external_artifact_versions ?? 0} />
          <Mini metric="Links" value={registrySummary?.artifact_links ?? 0} />
          <Mini metric="Contexts" value={registrySummary?.configuration_contexts ?? 0} />
          <Mini metric="Mappings" value={registrySummary?.configuration_item_mappings ?? 0} />
        </div>
        <Card>
          <CardHeader><div className="font-semibold">Federation snapshot</div></CardHeader>
          <CardBody className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
              ThreadLite keeps authoritative references and version mappings, not duplicated source files. Use the registry to connect requirements, blocks, test cases, and evidence back to their owning tools, while baselines remain frozen internal snapshots.
            </div>
            <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
              Open the registry to manage connectors, external artifacts, artifact links, review-gate configuration contexts, and the baseline relationship used for comparisons.
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${project.code} - ${project.name}`}
        description={project.description}
        action={
          <div className="flex flex-wrap gap-2">
            <Button href={`/projects/${project.id}/graph`} variant="secondary">Traceability graph</Button>
            <Button href={`/projects/${project.id}/matrix`}>Open matrix</Button>
            <Button href={`/projects/${project.id}/settings`} variant="secondary">Settings</Button>
            <Button href={api.exportProjectUrl(project.id)} variant="secondary">Export JSON</Button>
          </div>
        }
      />
      <ProjectTabs section={section} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">Project overview</div></CardHeader>
          <CardBody>
            <div className="grid gap-4 md:grid-cols-2">
              <Mini metric={labels.requirements} value={requirements.length} />
              <Mini metric={labels.blocks} value={blocks.length} />
              <Mini metric={labels.testCases} value={tests.length} />
              <Mini metric={labels.operationalRun} value={runs.length} />
            </div>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <Mini metric={`${labels.requirements} with components`} value={dashboard?.kpis.requirements_with_allocated_components ?? 0} />
              <Mini metric={`${labels.requirements} verified`} value={dashboard?.kpis.requirements_with_verifying_tests ?? 0} />
              <Mini metric={`${labels.requirements} at risk`} value={dashboard?.kpis.requirements_at_risk ?? 0} />
              <Mini metric={labels.kpi_open_changes} value={dashboard?.kpis.open_change_requests ?? 0} />
            </div>
            <div className="mt-5">
              <VerificationStatusBreakdownCard breakdown={dashboard?.verification_status_breakdown ?? { verified: 0, partially_verified: 0, at_risk: 0, failed: 0, not_covered: 0 }} title="Verification status distribution" />
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Quick links</div></CardHeader>
          <CardBody className="space-y-3">
            <Button href={`/projects/${project.id}/requirements`} className="w-full">{labels.requirements}</Button>
            <Button href={`/projects/${project.id}/blocks`} className="w-full" variant="secondary">{labels.blocks}</Button>
            <Button href={`/projects/${project.id}/components`} className="w-full" variant="secondary">Components</Button>
            <Button href={`/projects/${project.id}/software`} className="w-full" variant="secondary">Software</Button>
            <Button href={`/projects/${project.id}/tests`} className="w-full" variant="secondary">Tests</Button>
            <Button href={`/projects/${project.id}/validation`} className="w-full" variant="secondary">Validation</Button>
            <Button href={`/projects/${project.id}/simulation-evidence`} className="w-full" variant="secondary">{labels.simulationEvidence}</Button>
            <Button href={`/projects/${project.id}/fmi`} className="w-full" variant="secondary">FMI</Button>
            <Button href={`/projects/${project.id}/operational-evidence`} className="w-full" variant="secondary">{labels.operationalEvidence}</Button>
            <Button href={`/projects/${project.id}/import`} className="w-full" variant="secondary">Import data</Button>
            <Button href={`/projects/${project.id}/non-conformities`} className="w-full" variant="secondary">{labels.nonConformities}</Button>
            <Button href={`/projects/${project.id}/links`} className="w-full" variant="secondary">{labels.links}</Button>
            <Button href={`/projects/${project.id}/graph`} className="w-full" variant="secondary">Traceability graph</Button>
            <Button href={`/projects/${project.id}/sysml`} className="w-full" variant="secondary">SysML</Button>
            <Button href={`/projects/${project.id}/step-ap242`} className="w-full" variant="secondary">STEP AP242</Button>
            <Button href={`/projects/${project.id}/authoritative-sources`} className="w-full" variant="secondary">Authoritative Sources</Button>
            <Button href={`/projects/${project.id}/review-queue`} className="w-full" variant="secondary">Review Queue</Button>
            <Button href={api.exportProjectUrl(project.id)} className="w-full" variant="secondary">Export project bundle</Button>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function SimpleListPage({ project, section, title, description, items, createHref, createLabel }: { project: any; section: string; title: string; description: string; items: { key: string; label: string; status?: string; href: string }[]; createHref?: string; createLabel?: string }) {
  return (
    <div className="space-y-6">
      <SectionTitle title={`${project.code} - ${title}`} description={description} action={createHref ? <Button href={createHref}>{createLabel || "Create"}</Button> : undefined} />
      <ProjectTabs section={section} />
      <Card>
        <CardHeader><div className="font-semibold">{title}</div></CardHeader>
        <CardBody>{items.length ? <div className="space-y-3">{items.map((item) => <Link key={item.key} href={item.href} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50"><div className="flex items-center justify-between gap-4"><div><div className="font-semibold">{item.label}</div></div><Badge tone={itemTone(item.status)}>{item.status || "item"}</Badge></div></Link>)}</div> : <EmptyState title={`No ${title.toLowerCase()} yet`} description={description} action={createHref ? <Button href={createHref}>{createLabel || "Create first item"}</Button> : undefined} />}</CardBody>
      </Card>
    </div>
  );
}

function ObjectList({ items }: { items: { label: string; object_type: string }[] }) {
  return <div className="space-y-2">{items.map((item, index) => <div key={`${item.label}-${index}`} className="rounded-xl border border-line bg-panel2 p-3 text-sm">{item.label}</div>)}</div>;
}

function MappingContractView({ contract, labels }: { contract: SysMLMappingContractResponse | null; labels: { requirements: string; blocks: string } }) {
  if (!contract) {
    return <EmptyState title="No mapping contract yet" description="The mapping contract is derived from requirements, blocks, SysML relations, and block containments." />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><div className="font-semibold">SysML v2 mapping contract</div></CardHeader>
        <CardBody className="space-y-4">
          <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
            This view is a contract-shaped projection of the current internal model. It keeps requirement, block, satisfy, verify, deriveReqt, and contain mappings explicit without introducing a full SysML engine.
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Mini metric={labels.requirements} value={contract.summary.requirement_count} />
            <Mini metric={labels.blocks} value={contract.summary.block_count} />
            <Mini metric="Logical blocks" value={contract.summary.logical_block_count} />
            <Mini metric="Physical blocks" value={contract.summary.physical_block_count} />
            <Mini metric="Satisfy links" value={contract.summary.satisfy_relation_count} />
            <Mini metric="Verify links" value={contract.summary.verify_relation_count} />
            <Mini metric="DeriveReqt links" value={contract.summary.derive_relation_count} />
            <Mini metric="Contain links" value={contract.summary.contain_relation_count} />
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Requirement mappings</div></CardHeader>
          <CardBody className="space-y-4">
            {contract.requirements.map((row) => (
              <div key={row.requirement.id} className="rounded-xl border border-line bg-panel2 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold">{row.requirement.key} - {row.requirement.title}</div>
                    <div className="text-xs text-muted">SysML concept: {row.sysml_concept}</div>
                  </div>
                  <Badge tone="accent">{row.requirement.status}</Badge>
                </div>
                <MappingChipGroup title="satisfied by" items={row.satisfy_blocks} />
                <MappingChipGroup title="verified by" items={row.verify_tests} />
                <MappingChipGroup title="derived from" items={row.derived_from} />
                <MappingChipGroup title="derived requirements" items={row.derived_requirements} />
              </div>
            ))}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Block mappings</div></CardHeader>
          <CardBody className="space-y-4">
            {contract.blocks.map((row) => (
              <div key={row.block.id} className={`rounded-xl border p-4 ${row.abstraction_level === "physical" ? "border-amber-400/30 bg-amber-500/5" : "border-sky-400/30 bg-sky-500/5"}`}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold">{row.block.key} - {row.block.name}</div>
                    <div className="text-xs text-muted">SysML concept: {row.sysml_concept}</div>
                  </div>
                  <Badge tone={row.abstraction_level === "physical" ? "warning" : "accent"}>{row.profile_label}</Badge>
                </div>
                <MappingChipGroup title="contained blocks" items={row.contained_blocks} />
                <MappingChipGroup title="contained in" items={row.contained_in} />
                <MappingChipGroup title="satisfies requirements" items={row.satisfies_requirements} />
              </div>
            ))}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Explicit relations</div></CardHeader>
        <CardBody>
          <div className="space-y-2">
            {contract.relations.map((row) => (
              <div key={`${row.relation_type}-${row.source.object_id}-${row.target.object_id}`} className="flex flex-wrap items-center gap-2 rounded-xl border border-line bg-panel2 p-3 text-sm">
                <Badge tone="neutral">{row.relation_type}</Badge>
                <span className="font-medium">{row.source.label}</span>
                <span className="text-muted">â†’</span>
                <span className="font-medium">{row.target.label}</span>
                <span className="text-xs text-muted">{row.semantics}</span>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function StepAP242ContractView({ contract }: { contract: STEPAP242ContractResponse | null }) {
  if (!contract) {
    return <EmptyState title="No STEP AP242 contract yet" description="The AP242 placeholder contract is derived from components and cad_part external artifacts." />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><div className="font-semibold">STEP AP242 placeholder contract</div></CardHeader>
        <CardBody className="space-y-4">
          <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
            This is a lightweight AP242-style contract. It keeps part metadata, identifiers, and versions explicit while reusing the current ThreadLite component and external artifact model.
          </div>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Mini metric="Parts" value={contract.summary.physical_component_count} />
            <Mini metric="CAD artifacts" value={contract.summary.cad_artifact_count} />
            <Mini metric="Linked CAD artifacts" value={contract.summary.linked_cad_artifact_count} />
            <Mini metric="Identifiers" value={contract.summary.identifier_count} />
          </div>
        </CardBody>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Part metadata</div></CardHeader>
          <CardBody className="space-y-4">
            {contract.parts.map((row) => (
              <div key={row.component.id} className="rounded-xl border border-line bg-panel2 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold">{row.component.key} - {row.component.name}</div>
                    <div className="text-xs text-muted">AP242 concept: {row.profile_label}</div>
                  </div>
                  <Badge tone="warning">{row.status}</Badge>
                </div>
                <div className="mt-3 grid gap-2 text-sm">
                  <Row label="Part number" value={row.part_number || "-"} />
                  <Row label="Version" value={row.version} />
                  <Row label="Supplier" value={row.supplier || "-"} />
                </div>
                <div className="mt-3 space-y-2">
                  <div className="text-xs uppercase tracking-[0.2em] text-muted">Identifiers</div>
                  <div className="flex flex-wrap gap-2">
                    {row.identifiers.length ? row.identifiers.map((identifier) => (
                      <span key={`${row.component.id}-${identifier.kind}-${identifier.value}`} className="rounded-full border border-line bg-background px-2.5 py-1 text-xs">
                        {identifier.kind}: {identifier.value}
                      </span>
                    )) : <span className="text-xs text-muted">No AP242 identifiers yet.</span>}
                  </div>
                </div>
                <div className="mt-3 space-y-2">
                  <div className="text-xs uppercase tracking-[0.2em] text-muted">Linked cad_part artifacts</div>
                  {row.linked_cad_artifacts.length ? (
                    <div className="space-y-2">
                      {row.linked_cad_artifacts.map((artifact) => (
                        <Link key={artifact.id} href={`/external-artifacts/${artifact.id}`} className="block rounded-lg border border-line bg-background p-3 text-sm hover:border-accent/50">
                          <div className="font-medium">{artifact.external_id} - {artifact.name}</div>
                          <div className="text-xs text-muted">{artifact.connector_name || "No connector"} Â· {artifact.artifact_type} Â· versions {(artifact.versions || []).length}</div>
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-muted">No linked cad_part artifacts yet.</div>
                  )}
                </div>
              </div>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader><div className="font-semibold">AP242 relations</div></CardHeader>
          <CardBody className="space-y-3">
            {contract.relations.length ? contract.relations.map((row) => (
              <div key={`${row.relation_type}-${row.component.object_id}-${row.cad_artifact.id}`} className="rounded-xl border border-line bg-panel2 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone="neutral">{row.relation_type}</Badge>
                  <span className="font-medium">{row.component.label}</span>
                  <span className="text-muted">â†’</span>
                  <span className="font-medium">{row.cad_artifact.external_id}</span>
                </div>
                <div className="mt-2 text-xs text-muted">{row.semantics}</div>
              </div>
            )) : <EmptyState title="No AP242 relations yet" description="Link components to cad_part external artifacts to populate the placeholder contract." />}
          </CardBody>
        </Card>
      </div>
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

function MappingChipGroup({ title, items }: { title: string; items: { object_type: string; object_id: string; label: string }[] }) {
  if (!items.length) return <div className="mt-3 text-xs text-muted">{title}: none</div>;
  return (
    <div className="mt-3 space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => {
          const href = objectHref(item.object_type, item.object_id);
          const chip = <span className="rounded-full border border-line bg-background px-2.5 py-1 text-xs text-text">{item.label}</span>;
          return href ? <Link key={`${title}-${item.object_id}`} href={href}>{chip}</Link> : <span key={`${title}-${item.object_id}`}>{chip}</span>;
        })}
      </div>
    </div>
  );
}

function BlockTree({ nodes, depth = 0 }: { nodes: any[]; depth?: number }) {
  return (
    <div className="space-y-3">
      {nodes.map((node) => (
        <div
          key={node.block.id}
          className={`rounded-xl border p-3 ${node.block.abstraction_level === "physical" ? "border-amber-400/30 bg-amber-500/5" : "border-sky-400/30 bg-sky-500/5"}`}
          style={{ marginLeft: depth * 16 }}
        >
          <div className="flex items-center justify-between gap-4">
            <div className="font-semibold">{node.block.key} - {node.block.name}</div>
            <Badge tone={node.block.abstraction_level === "physical" ? "warning" : "accent"}>{node.block.abstraction_level}</Badge>
          </div>
          <div className="text-xs text-muted">{node.block.block_kind} / {node.block.status}</div>
          <div className="mt-1 text-xs text-muted">{node.block.abstraction_level === "physical" ? "Physical realization node" : "Logical architecture node"}</div>
          {node.satisfied_requirements?.length ? <div className="mt-2 text-xs text-muted">Satisfies {node.satisfied_requirements.length} requirements</div> : null}
          {node.linked_tests?.length ? <div className="mt-1 text-xs text-muted">Verified by {node.linked_tests.length} tests</div> : null}
          {node.children?.length ? <div className="mt-3 border-l border-line pl-4"><BlockTree nodes={node.children} depth={depth + 1} /></div> : null}
        </div>
      ))}
    </div>
  );
}

function Mini({ metric, value }: { metric: string; value: number }) {
  return <div className="rounded-2xl border border-line bg-panel2 p-4"><div className="text-xs uppercase tracking-[0.2em] text-muted">{metric}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}

function itemTone(status?: string) {
  if (status === "approved" || status === "passed" || status === "success") return "success";
  if (status === "in_review" || status === "degraded") return "warning";
  if (status === "failed" || status === "failure" || status === "rejected") return "danger";
  return "neutral";
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "operational_evidence") return `/operational-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  if (objectType === "block") return `/blocks/${objectId}`;
  if (objectType === "component") return `/components/${objectId}`;
  return null;
}

function buildQueryHref(base: string, params: { view?: string; layer?: string }) {
  const query = new URLSearchParams();
  if (params.view) query.set("view", params.view);
  if (params.layer && params.layer !== "all") query.set("layer", params.layer);
  const raw = query.toString();
  return raw ? `${base}?${raw}` : base;
}

function filterBlockTree(nodes: any[], layer: LayerFilter): any[] {
  if (layer === "all") return nodes;
  return nodes
    .map((node) => {
      const children = filterBlockTree(node.children || [], layer);
      const matches = node.block.abstraction_level === layer;
      if (!matches && !children.length) return null;
      return { ...node, children };
    })
    .filter(Boolean);
}

function buildRegistryLabels({ requirements, blocks, components, tests, runs, nonConformities, changeRequests, verificationEvidence, simulationEvidence, operationalEvidence, fmiContracts }: { requirements: any[]; blocks: any[]; components: any[]; tests: any[]; runs: any[]; nonConformities: any[]; changeRequests: any[]; verificationEvidence: any[]; simulationEvidence: any[]; operationalEvidence: any[]; fmiContracts: any[]; }) {
  const labels: Record<string, string> = {};
  const add = (type: string, id: string, label: string) => {
    if (id && label) labels[`${type}:${id}`] = label;
  };

  requirements.forEach((item) => add("requirement", String(item.id), `${item.key} - ${item.title}`));
  blocks.forEach((item) => add("block", String(item.id), `${item.key} - ${item.name}`));
  components.forEach((item) => add("component", String(item.id), `${item.key} - ${item.name}`));
  tests.forEach((item) => add("test_case", String(item.id), `${item.key} - ${item.title}`));
  runs.forEach((item) => add("operational_run", String(item.id), `${item.key} - ${item.notes || item.date}`));
  nonConformities.forEach((item) => add("non_conformity", String(item.id), `${item.key} - ${item.title}`));
  changeRequests.forEach((item) => add("change_request", String(item.id), `${item.key} - ${item.title}`));
  verificationEvidence.forEach((item) => add("verification_evidence", String(item.id), item.title));
  simulationEvidence.forEach((item) => add("simulation_evidence", String(item.id), item.title));
  operationalEvidence.forEach((item) => add("operational_evidence", String(item.id), item.title));
  fmiContracts.forEach((item) => add("fmi_contract", String(item.id), `${item.key} - ${item.name}`));
  return labels;
}



