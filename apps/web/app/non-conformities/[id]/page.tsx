import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { SimulationEvidenceMetadata } from "@/components/simulation-evidence-metadata";
import { VerificationEvidenceForm } from "@/components/verification-evidence-form";
import { NonConformityDispositionForm } from "@/components/non-conformity-disposition-form";

export const dynamic = "force-dynamic";

export default async function NonConformityPage({ params }: { params: { id: string } }) {
  const data = await api.nonConformity(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Non-conformity not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${data.non_conformity.key} - ${data.non_conformity.title}`}
        description={data.non_conformity.description}
      />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div className="font-semibold">Non-conformity record</div>
              <Button href={`/projects/${data.non_conformity.project_id}/non-conformities`} variant="secondary">Back to list</Button>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            <Row label="Status" value={<Badge>{data.non_conformity.status}</Badge>} />
            <Row
              label="Disposition"
              value={
                data.non_conformity.disposition ? (
                  <Badge tone={dispositionTone(data.non_conformity.disposition)}>{data.non_conformity.disposition}</Badge>
                ) : (
                  <span className="text-muted">No disposition selected</span>
                )
              }
            />
            <Row label="Severity" value={<Badge tone={severityTone(data.non_conformity.severity)}>{data.non_conformity.severity}</Badge>} />
            {data.non_conformity.review_comment ? <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">{data.non_conformity.review_comment}</div> : null}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Impact preview</div></CardHeader>
          <CardBody className="space-y-3">
            {(data.impact.likely_impacted || []).length ? (
              data.impact.likely_impacted.map((item: any) => (
                <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-muted">{item.object_type}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No impacted objects found yet.</div>
            )}
          </CardBody>
        </Card>
      </div>
      <Card>
        <CardHeader><div className="font-semibold">NCR decision</div></CardHeader>
        <CardBody className="space-y-4">
          <div className="text-sm text-muted">Choose the deviation handling decision. This stays separate from the NCR status and helps reviewers record whether the issue should be accepted, reworked, or rejected.</div>
          <NonConformityDispositionForm
            nonConformityId={data.non_conformity.id}
            currentDisposition={data.non_conformity.disposition}
            currentStatus={data.non_conformity.status}
          />
        </CardBody>
      </Card>
      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Impacted objects</div></CardHeader>
          <CardBody className="space-y-3">
            {data.related_requirements?.length ? (
              <div className="space-y-2">
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Related requirements</div>
                {data.related_requirements.map((item: any) => (
                  <Link key={item.object_id} href={`/requirements/${item.object_id}`} className="block rounded-xl border border-line bg-panel2 p-3 hover:border-accent/50">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-muted">{item.code || item.object_type}</div>
                  </Link>
                ))}
              </div>
            ) : null}
            {(data.links || []).length ? (
              data.links.map((link: any) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3">
                  <div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">→</span> {link.target_label || link.target_type}</div>
                  <div className="text-xs text-muted">{link.relation_type}</div>
                </div>
              ))
            ) : (
              <div className="text-sm text-muted">No impacted objects linked yet.</div>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Verification evidence</div></CardHeader>
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
                projectId={data.non_conformity.project_id}
                subjectType="non_conformity"
                subjectId={data.non_conformity.id}
                subjectLabel={`${data.non_conformity.key} - ${data.non_conformity.title}`}
              />
            </div>
          </CardBody>
        </Card>
      </div>
      <Card>
        <CardHeader><div className="font-semibold">Impact summary</div></CardHeader>
        <CardBody className="space-y-3">
          {data.impact_summary.map((item: any) => (
            <div key={item.object_id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="font-medium">{item.label}</div>
              <div className="text-xs text-muted">{item.object_type}</div>
            </div>
          ))}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}

function severityTone(severity: string) {
  if (severity === "critical") return "danger";
  if (severity === "high") return "warning";
  return "neutral";
}

function dispositionTone(disposition: string) {
  if (disposition === "accept") return "success";
  if (disposition === "rework") return "warning";
  return "danger";
}
