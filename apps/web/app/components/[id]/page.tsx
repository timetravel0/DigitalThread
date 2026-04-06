import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { RelationshipLinkForm } from "@/components/relationship-link-form";
import { ViewCue } from "@/components/view-cue";

export const dynamic = "force-dynamic";

export default async function ComponentPage({ params }: { params: { id: string } }) {
  const data = await api.component(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Component not found.</div>;
  const releasedBaselines = (data.impact.related_baselines || []).filter((baseline: any) => baseline.release_flag || baseline.status === "released");
  const requirements = await api.requirements(data.component.project_id).catch(() => []);
  const sysmlRelations = await api.sysmlRelations(data.component.project_id, { object_type: "component", object_id: data.component.id }).catch(() => []);
  const requirementLabels = new Map(requirements.map((item: any) => [item.id, `${item.key} - ${item.title}`]));
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
            <Row label="View layer" value={<Badge tone="warning">physical</Badge>} />
            <Row label="Metadata" value={<pre className="max-w-[320px] whitespace-pre-wrap text-right text-xs text-muted">{JSON.stringify(data.component.metadata_json, null, 2)}</pre>} />
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Impact preview</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.impact.likely_impacted || []).slice(0, 8).length ? (
              (data.impact.likely_impacted || []).slice(0, 8).map((item: any) => (
                <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-muted">{item.object_type}</div>
                </div>
              ))
            ) : (
              <EmptyState
                title="No impact preview yet"
                description="Components become understandable when requirements, blocks, and evidence point to them. Add those links so this realization object has a visible thread."
              />
            )}
          </CardBody>
        </Card>
      </div>
      <Card>
        <CardHeader><div className="font-semibold">Connect this component</div></CardHeader>
        <CardBody className="space-y-4">
          <div id="connect-requirements">
            <RelationshipLinkForm
              projectId={data.component.project_id}
              kind="sysml"
              sourceType="component"
              sourceId={data.component.id}
              sourceLabel={`${data.component.key} - ${data.component.name}`}
              relationType="trace"
              relationLabel="Trace to requirement"
              targetType="requirement"
              targetLabel="requirement"
              targets={requirements.map((item: any) => ({ id: item.id, label: `${item.key} - ${item.title}` }))}
              title="Requirements"
              description="Use this when the component realizes a requirement and should stay visible in the thread."
              emptyDescription="Requirements belong here when this component needs an explicit realization link."
              submitLabel="Link requirement"
              emptyAction={<Button href={`/projects/${data.component.project_id}/requirements`} variant="secondary">Open requirements</Button>}
            />
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><div className="font-semibold">SysML relations</div></CardHeader>
        <CardBody className="space-y-3">
          {sysmlRelations.length ? (
            sysmlRelations.map((relation: any) => {
              const sourceLabel = relation.source_type === "component" && relation.source_id === data.component.id
                ? `${data.component.key} - ${data.component.name}`
                : relation.source_type === "requirement"
                  ? requirementLabels.get(relation.source_id) || relation.source_type
                  : relation.source_type;
              const targetLabel = relation.target_type === "component" && relation.target_id === data.component.id
                ? `${data.component.key} - ${data.component.name}`
                : relation.target_type === "requirement"
                  ? requirementLabels.get(relation.target_id) || relation.target_type
                  : relation.target_type;
              return (
                <div key={relation.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{sourceLabel} <span className="text-muted">-&gt;</span> {targetLabel}</div>
                  <div className="text-xs text-muted">{relation.relation_type}{relation.rationale ? ` · ${relation.rationale}` : ""}</div>
                </div>
              );
            })
          ) : (
            <EmptyState
              title="No SysML relations yet"
              description="SysML relations belong here when this component realizes a requirement. Use the link form above to create the first one."
              action={<Button href="#connect-requirements" variant="secondary">Connect requirements</Button>}
            />
          )}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Released baselines</div></CardHeader>
        <CardBody className="space-y-3">
          <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">
            If this component belongs to a released baseline, any direct edit must route through a change request first.
          </div>
            {releasedBaselines.length ? (
              releasedBaselines.map((baseline: any) => (
                <Link key={baseline.id} href={`/baselines/${baseline.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold">{baseline.name}</div>
                    <div className="mt-1 text-sm text-muted">{baseline.description || "No description provided."}</div>
                  </div>
                  <Badge tone={baseline.release_flag ? "danger" : "neutral"}>{baseline.release_flag ? "Released" : baseline.status}</Badge>
                </div>
              </Link>
              ))
            ) : (
              <EmptyState
                title="No released baseline yet"
                description="Released baselines matter because they show whether this component is frozen in a review snapshot. When the component enters a released baseline, direct edits should route through change control."
              />
            )}
          </CardBody>
        </Card>
      {data.component.type === "software_module" ? (
        <Card>
          <CardHeader><div className="font-semibold">Software realization traceability</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This component is treated as an explicit software realization artifact, so requirements, blocks, and evidence can trace directly to it.</p>
            <p>Use the requirement and block traceability panel, together with the evidence section, to inspect how the software module fits the drone thread.</p>
            <div className="grid gap-2 rounded-xl border border-line bg-panel2 p-3 text-sm text-text">
              <Row label="Repository" value={data.component.metadata_json?.repository || data.component.metadata_json?.repository_ref || "Not recorded"} />
              <Row label="Branch" value={data.component.metadata_json?.branch || data.component.metadata_json?.ref || "Not recorded"} />
              <Row label="Entry point" value={data.component.metadata_json?.entry_point || data.component.metadata_json?.main_module || "Not recorded"} />
            </div>
          </CardBody>
        </Card>
      ) : null}
      <ViewCue layer="physical" />
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Requirement and block traceability</div></CardHeader>
          <CardBody className="space-y-3">
          {data.links.filter((link: any) => link.relation_type === "allocated_to" || link.relation_type === "satisfies" || link.relation_type === "uses").map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div>
                  <div className="text-xs text-muted">{link.relation_type}</div>
                </div>
              ))}
            {!data.links.filter((link: any) => link.relation_type === "allocated_to" || link.relation_type === "satisfies" || link.relation_type === "uses").length ? (
              <EmptyState
                title="No requirement or block traceability yet"
                description="Traceability links show how this component realizes requirements or supports blocks. Add a relation from the requirement or block detail page so the component is not isolated."
                action={<Button href="#connect-requirements" variant="secondary">Connect requirements</Button>}
              />
            ) : null}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Evidence</div></CardHeader>
          <CardBody className="space-y-4">
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
                    {Object.keys(evidence.metadata_json || {}).length ? (
                      <pre className="mt-2 overflow-auto rounded-lg border border-line bg-panel2 p-3 text-xs text-muted">{JSON.stringify(evidence.metadata_json, null, 2)}</pre>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No verification evidence linked yet"
                description="Evidence belongs here when you need to show why this component is acceptable. Add verification evidence from the component or related requirement so reviewers can inspect the proof trail."
              />
            )}
            <div className="rounded-xl border border-dashed border-line bg-panel2 p-4">
              <div className="mb-3 text-sm font-medium">Add verification evidence</div>
              <VerificationEvidenceForm
                projectId={data.component.project_id}
                subjectType="component"
                subjectId={data.component.id}
                subjectLabel={`${data.component.key} - ${data.component.name}`}
              />
            </div>
          </CardBody>
        </Card>
      </div>
      <Card>
        <CardHeader><div className="font-semibold">Traceability and change impacts</div></CardHeader>
        <CardBody className="space-y-3">
          {data.links.length ? data.links.map((link: any) => <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="text-xs text-muted">{link.relation_type}</div></div>) : <EmptyState title="No traceability yet" description="Components should be linked to the requirements, blocks, and evidence they realize. Add links from the relevant detail pages to make the component readable in the thread." />}
          {data.change_impacts.length ? data.change_impacts.map((impact: any) => <div key={impact.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{impact.impact_level} impact</div><div className="text-xs text-muted">{impact.notes}</div></div>) : <EmptyState title="No change impacts yet" description="Change impacts belong here when this component affects other objects. Add a change request or released baseline relationship so reviewers can see the blast radius." />}
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
