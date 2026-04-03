import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { ViewCue } from "@/components/view-cue";

export const dynamic = "force-dynamic";

export default async function ComponentPage({ params }: { params: { id: string } }) {
  const data = await api.component(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Component not found.</div>;
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
            {(data.impact.likely_impacted || []).slice(0, 8).map((item: any) => (
              <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{item.label}</div>
                <div className="text-xs text-muted">{item.object_type}</div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
      {data.component.type === "software_module" ? (
        <Card>
          <CardHeader><div className="font-semibold">Software realization</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This component is treated as a software realization artifact, so requirements, blocks, and evidence can trace directly to it.</p>
            <p>Use the linked evidence panel below to connect telemetry, simulation, or test evidence to the software module.</p>
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
              <div className="text-sm text-muted">No requirement or block traceability linked yet.</div>
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
              <div className="text-sm text-muted">No evidence linked yet.</div>
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
          {data.links.map((link: any) => <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="text-xs text-muted">{link.relation_type}</div></div>)}
          {data.change_impacts.map((impact: any) => <div key={impact.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{impact.impact_level} impact</div><div className="text-xs text-muted">{impact.notes}</div></div>)}
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
