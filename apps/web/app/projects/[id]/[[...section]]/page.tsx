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
import { OnboardingWizard } from "@/components/onboarding-wizard";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";
import { SimulationEvidenceForm } from "@/components/simulation-evidence-form";
import { ValidationWorkbench } from "@/components/validation-workbench";
import { ProjectHealthCard } from "@/components/project-health-card";
import { SectionIntroCard } from "@/components/project-home-guide";

export const dynamic = "force-dynamic";

type LayerFilter = "all" | "logical" | "physical";
const requirementsEmptyDescription: Record<"engineering" | "manufacturing" | "personal" | "custom", string> = {
  engineering:
    "Requirements define what your system must do or satisfy. Start here - blocks and tests gain meaning only when linked to requirements.",
  manufacturing:
    "Specifications define the product's quality, process, and regulatory constraints. Add at least one before defining components.",
  personal:
    "Goals define what you want your project to achieve. Start by writing one clear objective - everything else connects to it.",
  custom:
    "Define the constraints and objectives your system must satisfy. All other items connect back to these.",
};

const blocksEmptyDescription: Record<"engineering" | "manufacturing" | "personal" | "custom", string> = {
  engineering:
    "Blocks represent physical or logical parts of your system. Add blocks and link them to requirements to track allocation coverage.",
  manufacturing:
    "Components represent the physical parts, assemblies, or production stages in your process. Link them to specifications to track compliance.",
  personal:
    "Elements are the devices, services, or modules in your setup. Add them and connect them to your goals.",
  custom:
    "Add the parts or subsystems that compose your system, then link them to requirements.",
};

const testsEmptyDescription: Record<"engineering" | "manufacturing" | "personal" | "custom", string> = {
  engineering:
    "Test cases define how each requirement will be verified. Without tests, requirements remain unverified in the Digital Thread.",
  manufacturing:
    "Quality checks define the inspection and testing procedures for each specification. Link them to ensure full coverage.",
  personal:
    "Checks are the verifications you run to confirm your setup works as intended. Connect each check to a goal.",
  custom:
    "Define how each requirement will be verified. Link test cases to requirements to track verification coverage.",
};

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
  const threadCounts = {
    requirements: requirements.length,
    blocks: blocks.length,
    tests: tests.length,
    links: links.length + artifactLinks.length + sysmlRelations.length,
    evidence: verificationEvidence.length + simulationEvidence.length + operationalEvidence.length,
    baselines: baselines.length,
    changeRequests: changeRequests.length,
  };

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
          <MappingContractView contract={mappingContract} labels={labels} projectId={project.id} />
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
        <SectionIntroCard
          title="How to use this view"
          description="This page shows physical parts, identifiers, and CAD artifacts in one place. Use it when you want to connect the product structure back to the external design source."
          nextStep="Next step: open a part card, then follow its linked CAD artifact if you need the originating model data."
        />
          <StepAP242ContractView contract={contract} projectId={project.id} />
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
        <SectionIntroCard
          title="How to read the graph"
          description="Start from the focus that matters most, then click any box to shrink the view to its connected neighborhood. The graph is meant to answer 'why is this connected?' rather than show every object equally."
          nextStep="Next step: click a requirement or block to follow its linked realization and verification path."
        />
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
          projectId={project.id}
          labels={labels}
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
    return (
      <SimpleListPage
        project={project}
        section={section}
        title="Review Queue"
        description="Items waiting for approval, rejection, or further analysis before they can move forward."
        intro={{
          title: "Review work in one place",
          description: "This queue helps reviewers see what needs attention now. It matters because unresolved items slow the thread and hide the next decision.",
          nextStep: "Next step: open the item with the highest priority and decide whether it should move forward, go back, or be revised.",
        }}
        items={(reviewQueue?.items || []).map((item) => ({ key: item.key, label: `${item.object_type}: ${item.title}`, status: item.status, href: `/${item.object_type === "test_case" ? "test-cases" : item.object_type === "block" ? "blocks" : "requirements"}/${item.id}` }))}
        emptyTitle="Nothing waiting for review"
        emptyDescription="This queue fills when requirements, blocks, or test cases are ready for a decision. It matters because reviewers need one place to see what should be approved, revised, or sent back."
        emptyAction={<Button href={`/projects/${project.id}/change-requests`} variant="secondary">Open change requests</Button>}
      />
    );
  }

  if (section === "validation") {
    return (
      <div className="space-y-6">
        <SectionTitle
          title={`${project.code} - Validation`}
          description="A SidSat-style validation cockpit for non-technical reviewers. Pick a target requirement, choose a focus, and run a lightweight validation check with immediate alerts."
        />
        <ProjectTabs section={section} />
        <SectionIntroCard
          title="What this page does"
          description="Use the validation cockpit when you want a guided check against one requirement. It surfaces alerts and threshold checks without asking you to interpret the full model."
          nextStep="Next step: select a target requirement, then start validation."
        />
        <ValidationWorkbench
          projectId={project.id}
          projectCode={project.code}
          projectName={project.name}
          requirements={requirements}
        />
      </div>
    );
  }

    if (section === "requirements") {
      const profileKey = project.domain_profile as keyof typeof requirementsEmptyDescription;
      return (
          <SimpleListPage
          project={project}
          section={section}
          title={labels.requirements}
          description="Editable requirements with approval workflow. This is the anchor point for the rest of the thread."
          intro={{
            title: `${labels.requirements} first`,
            description: `Capture the need, goal, or specification that anchors this project. It matters because every ${labels.block.toLowerCase()} and ${labels.testCase.toLowerCase()} should trace back to something explicit here.`,
            nextStep: `Next step: create your first ${labels.requirement.toLowerCase()}, then connect it to the realization and verification work.`,
          }}
          items={requirements.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/requirements/${item.id}` }))}
          createHref={`/requirements/new?project=${project.id}`}
          createLabel={`Create ${labels.requirement}`}
          emptyTitle={`No ${labels.requirements} yet`}
          emptyDescription={requirementsEmptyDescription[profileKey] ?? requirementsEmptyDescription.engineering}
          emptyActionLabel={`+ Add ${labels.requirements}`}
        />
      );
    }
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
        <SectionIntroCard
          title="What to look for"
          description="This section makes software realization explicit so requirements and evidence do not disappear inside a generic component list."
          nextStep="Next step: open a software module, then follow its requirement links and evidence records."
        />
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
                        <div className="text-sm text-muted">No requirement, block, or trace links found for this software module yet. Software realization becomes useful when the module is linked back to the requirements or blocks it implements.</div>
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
                        <div className="text-sm text-muted">No verification evidence linked yet. Add evidence when the software module has a test, review, or inspection record that proves it behaves as expected.</div>
                      )}
                    </div>
                    <Button href={`/components/${detail.component.id}`} variant="secondary">Open component detail</Button>
                  </CardBody>
                </Card>
              );
            })}
          </div>
        ) : (
          <EmptyState
            title="No software realization yet"
            description="Software belongs here when the project needs explicit code-to-thread traceability. Create a component with type software_module so requirements, blocks, and evidence can point to a real software artifact."
            action={<Button href={`/components/new?project=${project.id}`}>Create software component</Button>}
          />
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
            description={layer === "all"
              ? "Define the parts and elements that realize the thread. Use the layer switch to keep logical intent and physical realization readable."
              : `${layer === "logical" ? "Logical architecture" : "Physical realization"} blocks only.`}
            action={<Button href={`/blocks/new?project=${project.id}`}>Create</Button>}
          />
          <ProjectTabs section={section} />
          <SectionIntroCard
            title={`${labels.blocks} in context`}
            description={`This is where you define the parts or elements that realize the thread. It matters because requirements stay abstract until they are tied to something concrete here.`}
            nextStep={`Next step: create a ${labels.block.toLowerCase()} or component that realizes the first ${labels.requirement.toLowerCase()}, then link it back.`}
          />
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
                <EmptyState
                  title={layer === "all" ? `No ${labels.blocks} yet` : `No ${labels.blocks} in this layer yet`}
                  description={`${blocksEmptyDescription[project.domain_profile as keyof typeof blocksEmptyDescription] ?? blocksEmptyDescription.engineering}${layer === "all" ? "" : " Switch layers to see the other architectural view or create additional blocks to populate this one."}`}
                  action={<Button href={`/blocks/new?project=${project.id}`}>+ Add {labels.blocks}</Button>}
                />
              )}
            </CardBody>
          </Card>
        </div>
      );
    }
  if (section === "components") return <SimpleListPage project={project} section={section} title="Components" description="Realization objects, including software modules." items={components.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.name}`, status: item.status, href: `/components/${item.id}` }))} />;
  if (section === "tests") {
        const profileKey = project.domain_profile as keyof typeof testsEmptyDescription;
        return (
          <SimpleListPage
            project={project}
            section={section}
            title={labels.testCases}
            description="Verification artifacts with workflow and history. Use them to prove the thread works, not just that it was described."
            intro={{
              title: `${labels.testCases} first`,
              description: `Create the checks that prove each ${labels.requirements.toLowerCase()} or goal is met. Keep them linked so coverage stays visible in the thread and reviewers can see what still needs proof.`,
              nextStep: `Next step: add the first ${labels.testCase.toLowerCase()} for a requirement you already care about, then connect it back to the thread.`,
            }}
            items={tests.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/test-cases/${item.id}` }))}
            createHref={`/test-cases/new?project=${project.id}`}
            createLabel={`Create ${labels.testCase}`}
            emptyTitle={`No ${labels.testCases} yet`}
          emptyDescription={testsEmptyDescription[profileKey] ?? testsEmptyDescription.engineering}
          emptyActionLabel={`+ Add ${labels.testCases}`}
        />
      );
    }
  if (section === "runs") return <SimpleListPage project={project} section={section} title={`${labels.operationalRun}s`} description="Field evidence and telemetry." items={runs.map((run: any) => ({ key: run.key, label: `${run.key} - ${run.notes}`, status: run.outcome, href: `/operational-runs/${run.id}` }))} createHref={`/operational-runs/new?project=${project.id}`} />;
  if (section === "operational-evidence") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - ${labels.operationalEvidence}`} description="Batch-style operational feedback linked to requirements and verification evidence." />
        <ProjectTabs section={section} />
        <SectionIntroCard
          title="What to inspect here"
          description="Operational evidence captures field feedback in batches. Open a card to see the source, the observation window, and how the batch relates back to the thread."
          nextStep="Next step: add a batch when you need to capture operational observations that should influence verification."
        />
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
              <EmptyState title="No operational evidence yet" description="Operational evidence belongs here when field observations or telemetry need to stay connected to the requirement or verification record they support. Add the first batch to capture source, coverage window, and observations." />
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
        <SectionIntroCard
          title="What to inspect here"
          description="Simulation evidence records the model, scenario, inputs, observed behavior, and outcome. Use it when you want simulation feedback to stay separate from generic verification evidence."
          nextStep="Next step: create a simulation record and connect it to the requirement and test it explains."
        />
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
              <EmptyState title="No simulation evidence yet" description="Simulation evidence belongs here when a model or scenario explains why the requirement behaves as it does. Add the first record to capture model, scenario, inputs, and observed behavior." />
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
        <SectionTitle title={`${project.code} - FMI`} description="A lightweight interoperability surface for simulation records, with explicit model reference fields." />
        <ProjectTabs section={section} />
        <SectionIntroCard
          title="Why this exists"
          description="The FMI contract gives simulation a model-reference surface without adding a full interoperability runtime. Use it as the explicit anchor for simulation evidence."
          nextStep="Next step: create a contract only when you need a named model reference for simulation evidence."
        />
        <Card>
          <CardHeader><div className="font-semibold">FMI contracts</div></CardHeader>
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
              <EmptyState
                title="No FMI contract yet"
                description="FMI contracts belong here when a simulation needs an explicit model-reference anchor. Create one only when you need to connect simulation evidence to a specific model or adapter profile."
                action={<Button href="#add-fmi-contract" variant="secondary">Open FMI form</Button>}
              />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Add FMI contract</div></CardHeader>
          <CardBody>
            <div id="add-fmi-contract">
            <FMIContractForm projectId={project.id} />
            </div>
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
        <SectionIntroCard
          title="How to use the registry"
          description="Use the registry when you want a flat, filterable list instead of a graph. It is useful for reviewing a specific relation type without navigating the full workspace."
          nextStep="Next step: filter by links or evidence, then open the row that best matches the object you need."
        />
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
    if (section === "baselines") return <SimpleListPage project={project} section={section} title={labels.baselines} description="Approved-only snapshots of internal state. Use baselines when you need a frozen point of comparison for review or release." intro={{ title: `${labels.baselines} as review snapshots`, description: "A baseline captures the project state at a known point in time. It matters because reviews and comparisons only work when the snapshot is explicit.", nextStep: "Next step: prepare a configuration context and release a baseline when the project is ready for review." }} items={baselines.map((baseline: any) => ({ key: baseline.id, label: baseline.name, status: baseline.status, href: `/baselines/${baseline.id}` }))} emptyTitle={`No ${labels.baselines} yet`} emptyDescription="Baselines are frozen review snapshots. Create a configuration context first, then release a baseline when you need a stable point of comparison." emptyAction={<Button href={`/projects/${project.id}/authoritative-sources?tab=configuration-contexts`} variant="secondary">Open authoritative sources</Button>} />;
    if (section === "non-conformities") return <SimpleListPage project={project} section={section} title={labels.nonConformities} description="First-class issue records with their own lifecycle and traceability. Use them when the implementation or test result does not match the design intent." intro={{ title: `${labels.nonConformities} explain the gap`, description: "A non-conformity records what failed, why it matters, and what decision was made. It keeps the issue linked to the original requirement so impact stays visible.", nextStep: "Next step: open a non-conformity when a design or test result does not match the expectation." }} items={nonConformities.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/non-conformities/${item.id}` }))} emptyTitle={`No ${labels.nonConformities} yet`} emptyDescription="Non-conformities belong here when the thread reveals a deviation between design intent and what was actually found. Record the gap so the original requirement stays linked to the issue." emptyAction={<Button href={`/projects/${project.id}/tests`} variant="secondary">Review tests</Button>} />;
    if (section === "change-requests") return <SimpleListPage project={project} section={section} title={labels.changeRequests} description="Impact-driven change management. Use this area when a requirement, block, or test needs to evolve after review." intro={{ title: `${labels.changeRequests} manage change`, description: "A change request captures a proposed evolution to the thread and the impact it creates. It matters because nothing in the Digital Thread should change without a visible reason and review path.", nextStep: "Next step: draft a change request when the current design needs to move forward or be corrected." }} items={changeRequests.map((cr: any) => ({ key: cr.key, label: `${cr.key} - ${cr.title}`, status: cr.status, href: `/change-requests/${cr.id}` }))} emptyTitle={`No ${labels.changeRequests} yet`} emptyDescription="Change requests belong here when the thread needs to evolve after review. Use them to explain the reason for the change and keep the impact visible." emptyAction={<Button href={`/projects/${project.id}/requirements`} variant="secondary">Review requirements</Button>} />;
  if (section === "authoritative-sources") {
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - Authoritative Sources`} description="Federated metadata pointers, connectors, configuration contexts, and the review-gate bridge to baselines." action={<Button href={`/projects/${project.id}/authoritative-sources`}>Open registry</Button>} />
        <ProjectTabs section={section} />
        <SectionIntroCard
          title="What this page is for"
          description="This area keeps authoritative pointers and review-gate snapshots explicit. Use it when you need to inspect where the project data is owned and how it is frozen for review."
          nextStep="Next step: open the registry if you need connectors, external artifacts, or configuration contexts."
        />
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
    <OnboardingWizard projectId={project.id} profile={project.domain_profile} labels={labels}>
      <div className="space-y-6">
        <ProjectHealthCard dashboard={dashboard} labels={labels} projectId={project.id} project={project} counts={threadCounts} />
        <ProjectTabs section={section} />
      </div>
    </OnboardingWizard>
  );
}

function SimpleListPage({ project, section, title, description, items, createHref, createLabel, emptyTitle, emptyDescription, emptyActionLabel, emptyAction, intro }: { project: any; section: string; title: string; description: string; items: { key: string; label: string; status?: string; href: string }[]; createHref?: string; createLabel?: string; emptyTitle?: string; emptyDescription?: string; emptyActionLabel?: string; emptyAction?: any; intro?: { title: string; description: string; nextStep?: string } }) {
  return (
    <div className="space-y-6">
      <SectionTitle title={`${project.code} - ${title}`} description={description} action={createHref ? <Button href={createHref}>{createLabel || "Create"}</Button> : undefined} />
      <ProjectTabs section={section} />
      {intro ? <SectionIntroCard title={intro.title} description={intro.description} nextStep={intro.nextStep} /> : null}
      <Card>
        <CardHeader><div className="font-semibold">{title}</div></CardHeader>
        <CardBody>{items.length ? <div className="space-y-3">{items.map((item) => <Link key={item.key} href={item.href} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50"><div className="flex items-center justify-between gap-4"><div><div className="font-semibold">{item.label}</div></div><Badge tone={itemTone(item.status)}>{item.status || "item"}</Badge></div></Link>)}</div> : <EmptyState title={emptyTitle || `No ${title.toLowerCase()} yet`} description={composeEmptyDescription(emptyDescription, intro?.description, intro?.nextStep, description)} action={emptyAction || (createHref ? <Button href={createHref}>{emptyActionLabel || createLabel || "Create first item"}</Button> : undefined)} />}</CardBody>
      </Card>
    </div>
  );
}

function composeEmptyDescription(emptyDescription?: string, introDescription?: string, introNextStep?: string, fallback?: string) {
  const base = emptyDescription || introDescription || fallback || "";
  const next = introNextStep ? ` ${introNextStep}` : "";
  return `${base}${next}`.trim();
}

function ObjectList({ items }: { items: { label: string; object_type: string }[] }) {
  return <div className="space-y-2">{items.map((item, index) => <div key={`${item.label}-${index}`} className="rounded-xl border border-line bg-panel2 p-3 text-sm">{item.label}</div>)}</div>;
}

function MappingContractView({ contract, labels, projectId }: { contract: SysMLMappingContractResponse | null; labels: { requirements: string; blocks: string }; projectId: string }) {
  if (!contract) {
    return (
      <EmptyState
        title="No mapping contract yet"
        description="The mapping contract belongs here when requirements, blocks, and their SysML relations need a reviewable structure. Add requirements and blocks first, then revisit this view to see the derived mappings."
        action={<Button href={`/projects/${projectId}/requirements`} variant="secondary">Open requirements</Button>}
      />
    );
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

function StepAP242ContractView({ contract, projectId }: { contract: STEPAP242ContractResponse | null; projectId: string }) {
  if (!contract) {
    return (
      <EmptyState
        title="No STEP AP242 contract yet"
        description="The AP242 contract belongs here when physical components need explicit CAD pointers and part metadata. Create components first, then link their cad_part artifacts in authoritative sources."
        action={<div className="flex flex-wrap gap-2"><Button href={`/projects/${projectId}/components`} variant="secondary">Open components</Button><Button href={`/projects/${projectId}/authoritative-sources`} variant="secondary">Open authoritative sources</Button></div>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><div className="font-semibold">STEP AP242 contract</div></CardHeader>
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
                      )) : (
                        <EmptyState
                          title="No AP242 identifiers yet"
                          description="Identifiers belong here when a physical component needs a part number, drawing reference, or another AP242-style label. Add the identifier on the component detail page so it stays readable across tools."
                          action={<Button href={`/projects/${projectId}/components`} variant="secondary">Open components</Button>}
                        />
                      )}
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
                      <EmptyState
                        title="No linked cad_part artifacts yet"
                        description="Link a cad_part artifact when the physical component needs an external CAD source of truth. The AP242 contract becomes useful once the CAD pointer is explicit."
                        action={<Button href={`/projects/${projectId}/authoritative-sources`} variant="secondary">Open authoritative sources</Button>}
                      />
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
            )) : <EmptyState title="No AP242 relations yet" description="AP242 relations belong here when physical components are linked to cad_part external artifacts. Add the CAD pointer in authoritative sources so the interoperability view can show the real source of truth." action={<Button href={`/projects/${projectId}/authoritative-sources`} variant="secondary">Open registry</Button>} />}
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



