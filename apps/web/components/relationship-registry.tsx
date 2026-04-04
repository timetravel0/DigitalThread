import type { ReactNode } from "react";
import Link from "next/link";
import { Badge, Card, CardBody, CardHeader, EmptyState } from "@/components/ui";

type RegistryKind = "all" | "requirements" | "links" | "evidence";
type LinkKind = "all" | "generic" | "sysml" | "artifact";
type EvidenceKind = "all" | "verification" | "simulation" | "operational";

type LabelMap = Record<string, string>;

type RelationshipRegistryProps = {
  projectId: string;
  kind: RegistryKind;
  linkKind: LinkKind;
  evidenceKind: EvidenceKind;
  labels: LabelMap;
  requirements: any[];
  links: any[];
  sysmlRelations: any[];
  artifactLinks: any[];
  verificationEvidence: any[];
  simulationEvidence: any[];
  operationalEvidence: any[];
};

export function RelationshipRegistry({
  projectId,
  kind,
  linkKind,
  evidenceKind,
  labels,
  requirements,
  links,
  sysmlRelations,
  artifactLinks,
  verificationEvidence,
  simulationEvidence,
  operationalEvidence,
}: RelationshipRegistryProps) {
  const counts = {
    requirements: requirements.length,
    links: links.length,
    sysmlRelations: sysmlRelations.length,
    artifactLinks: artifactLinks.length,
    evidence: verificationEvidence.length + simulationEvidence.length + operationalEvidence.length,
  };

  const showRequirements = kind === "all" || kind === "requirements";
  const showLinks = kind === "all" || kind === "links";
  const showEvidence = kind === "all" || kind === "evidence";

  const baseHref = `/projects/${projectId}/links`;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader><div className="font-semibold">Registry summary</div></CardHeader>
        <CardBody className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <Stat label="Requirements" value={counts.requirements} href={buildHref(baseHref, { kind: "requirements" })} active={kind === "requirements"} />
          <Stat label="Links" value={counts.links + counts.sysmlRelations + counts.artifactLinks} href={buildHref(baseHref, { kind: "links" })} active={kind === "links"} />
          <Stat label="Verification evidence" value={verificationEvidence.length} href={buildHref(baseHref, { kind: "evidence", evidence: "verification" })} active={kind === "evidence" && evidenceKind === "verification"} />
          <Stat label="Simulation evidence" value={simulationEvidence.length} href={buildHref(baseHref, { kind: "evidence", evidence: "simulation" })} active={kind === "evidence" && evidenceKind === "simulation"} />
          <Stat label="Operational evidence" value={operationalEvidence.length} href={buildHref(baseHref, { kind: "evidence", evidence: "operational" })} active={kind === "evidence" && evidenceKind === "operational"} />
        </CardBody>
      </Card>

      <Card>
        <CardHeader><div className="font-semibold">Filters</div></CardHeader>
        <CardBody className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <FilterPill href={buildHref(baseHref, {})} active={kind === "all"}>All</FilterPill>
            <FilterPill href={buildHref(baseHref, { kind: "requirements" })} active={kind === "requirements"}>Requirements</FilterPill>
            <FilterPill href={buildHref(baseHref, { kind: "links" })} active={kind === "links"}>Links</FilterPill>
            <FilterPill href={buildHref(baseHref, { kind: "evidence" })} active={kind === "evidence"}>Evidence</FilterPill>
          </div>

          {kind === "links" ? (
            <div className="flex flex-wrap gap-2">
              <FilterPill href={buildHref(baseHref, { kind: "links" })} active={linkKind === "all"}>All links</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "links", relation: "generic" })} active={linkKind === "generic"}>Generic links</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "links", relation: "sysml" })} active={linkKind === "sysml"}>SysML relations</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "links", relation: "artifact" })} active={linkKind === "artifact"}>Artifact links</FilterPill>
            </div>
          ) : null}

          {kind === "evidence" ? (
            <div className="flex flex-wrap gap-2">
              <FilterPill href={buildHref(baseHref, { kind: "evidence" })} active={evidenceKind === "all"}>All evidence</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "evidence", evidence: "verification" })} active={evidenceKind === "verification"}>Verification</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "evidence", evidence: "simulation" })} active={evidenceKind === "simulation"}>Simulation</FilterPill>
              <FilterPill href={buildHref(baseHref, { kind: "evidence", evidence: "operational" })} active={evidenceKind === "operational"}>Operational</FilterPill>
            </div>
          ) : null}
        </CardBody>
      </Card>

      {showRequirements ? (
        <Card>
          <CardHeader><div className="font-semibold">Requirements</div></CardHeader>
          <CardBody>
            {requirements.length ? (
              <div className="space-y-3">
                {requirements.map((req) => (
                  <Link key={req.id} href={`/requirements/${req.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{req.key} - {req.title}</div>
                        <div className="text-xs text-muted">{req.category} · {req.priority} · v{req.version}</div>
                      </div>
                      <Badge tone={badgeTone(req.status)}>{req.status}</Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No requirements found" description="Create requirements to populate the registry." />
            )}
          </CardBody>
        </Card>
      ) : null}

      {showLinks ? (
        <Card>
          <CardHeader><div className="font-semibold">Links</div></CardHeader>
          <CardBody className="space-y-6">
            {(linkKind === "all" || linkKind === "generic") ? (
              <RegistryLinkGroup
                title="Generic links"
                emptyTitle="No generic links yet"
                items={links}
                renderItem={(item) => (
                  <div className="rounded-xl border border-line bg-panel2 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="neutral">{item.relation_type}</Badge>
                      {objectChip(labels, item.source_type, item.source_id, item.source_label || item.source_type)}
                      <span className="text-muted">→</span>
                      {objectChip(labels, item.target_type, item.target_id, item.target_label || item.target_type)}
                    </div>
                    {item.rationale ? <div className="mt-2 text-xs text-muted">{item.rationale}</div> : null}
                  </div>
                )}
              />
            ) : null}

            {(linkKind === "all" || linkKind === "sysml") ? (
              <RegistryLinkGroup
                title="SysML relations"
                emptyTitle="No SysML relations yet"
                items={sysmlRelations}
                renderItem={(item) => (
                  <div className="rounded-xl border border-line bg-panel2 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="accent">{item.relation_type}</Badge>
                      {objectChip(labels, item.source_type, item.source_id, item.source_type)}
                      <span className="text-muted">→</span>
                      {objectChip(labels, item.target_type, item.target_id, item.target_type)}
                    </div>
                    {item.rationale ? <div className="mt-2 text-xs text-muted">{item.rationale}</div> : <div className="mt-2 text-xs text-muted">{describeSysMLRelation(item.relation_type)}</div>}
                  </div>
                )}
              />
            ) : null}

            {(linkKind === "all" || linkKind === "artifact") ? (
              <RegistryLinkGroup
                title="Artifact links"
                emptyTitle="No artifact links yet"
                items={artifactLinks}
                renderItem={(item) => (
                  <div className="rounded-xl border border-line bg-panel2 p-4">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="warning">{item.relation_type}</Badge>
                      {objectChip(labels, item.internal_object_type, item.internal_object_id, item.internal_object_label || item.internal_object_type)}
                      <span className="text-muted">→</span>
                      <Link href={`/external-artifacts/${item.external_artifact_id}`} className="font-medium text-accent hover:underline">
                        {item.external_artifact_name || item.external_artifact_id}
                      </Link>
                    </div>
                    <div className="mt-2 text-xs text-muted">
                      {item.external_artifact_version_label ? `Version: ${item.external_artifact_version_label}` : "No external artifact version selected"}
                      {item.connector_name ? ` · Connector: ${item.connector_name}` : ""}
                    </div>
                  </div>
                )}
              />
            ) : null}
          </CardBody>
        </Card>
      ) : null}

      {showEvidence ? (
        <Card>
          <CardHeader><div className="font-semibold">Evidence</div></CardHeader>
          <CardBody className="space-y-6">
            {(evidenceKind === "all" || evidenceKind === "verification") ? (
              <RegistryEvidenceGroup
                title="Verification evidence"
                emptyTitle="No verification evidence yet"
                items={verificationEvidence}
                renderItem={(item) => (
                  <Link href={`/verification-evidence/${item.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{item.title}</div>
                        <div className="text-xs text-muted">{item.evidence_type} · {item.summary}</div>
                      </div>
                      <Badge tone={badgeTone(item.evidence_type)}>{item.evidence_type}</Badge>
                    </div>
                  </Link>
                )}
              />
            ) : null}

            {(evidenceKind === "all" || evidenceKind === "simulation") ? (
              <RegistryEvidenceGroup
                title="Simulation evidence"
                emptyTitle="No simulation evidence yet"
                items={simulationEvidence}
                renderItem={(item) => (
                  <Link href={`/simulation-evidence/${item.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{item.title}</div>
                        <div className="text-xs text-muted">{item.model_reference} · {item.scenario_name} · {item.result}</div>
                      </div>
                      <Badge tone={badgeTone(item.result)}>{item.result}</Badge>
                    </div>
                  </Link>
                )}
              />
            ) : null}

            {(evidenceKind === "all" || evidenceKind === "operational") ? (
              <RegistryEvidenceGroup
                title="Operational evidence"
                emptyTitle="No operational evidence yet"
                items={operationalEvidence}
                renderItem={(item) => (
                  <Link href={`/operational-evidence/${item.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{item.title}</div>
                        <div className="text-xs text-muted">{item.source_name} · {item.source_type} · {item.quality_status}</div>
                      </div>
                      <Badge tone={badgeTone(item.quality_status)}>{item.quality_status}</Badge>
                    </div>
                  </Link>
                )}
              />
            ) : null}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function RegistryLinkGroup({ title, emptyTitle, items, renderItem }: { title: string; emptyTitle: string; items: any[]; renderItem: (item: any) => ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <div className="font-medium">{title}</div>
        <div className="text-xs text-muted">{items.length} records</div>
      </div>
      {items.length ? <div className="space-y-3">{items.map((item) => <div key={item.id}>{renderItem(item)}</div>)}</div> : <EmptyState title={emptyTitle} description={`No ${title.toLowerCase()} match the current filters.`} />}
    </section>
  );
}

function RegistryEvidenceGroup({ title, emptyTitle, items, renderItem }: { title: string; emptyTitle: string; items: any[]; renderItem: (item: any) => ReactNode }) {
  return (
    <section className="space-y-3">
      <div>
        <div className="font-medium">{title}</div>
        <div className="text-xs text-muted">{items.length} records</div>
      </div>
      {items.length ? <div className="space-y-3">{items.map((item) => <div key={item.id}>{renderItem(item)}</div>)}</div> : <EmptyState title={emptyTitle} description={`No ${title.toLowerCase()} match the current filters.`} />}
    </section>
  );
}

function Stat({ label, value, href, active }: { label: string; value: number; href: string; active?: boolean }) {
  return (
    <Link href={href} className={`rounded-2xl border p-4 ${active ? "border-accent bg-accent/10" : "border-line bg-panel2 hover:border-accent/50"}`}>
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </Link>
  );
}

function FilterPill({ href, active, children }: { href: string; active?: boolean; children: ReactNode }) {
  return (
    <Link href={href} className={`rounded-full border px-3 py-1.5 text-sm ${active ? "border-accent bg-accent/10 text-accent" : "border-line text-text hover:bg-white/5"}`}>
      {children}
    </Link>
  );
}

function buildHref(baseHref: string, params: { kind?: string; relation?: string; evidence?: string }) {
  const search = new URLSearchParams();
  if (params.kind && params.kind !== "all") search.set("kind", params.kind);
  if (params.relation && params.relation !== "all") search.set("relation", params.relation);
  if (params.evidence && params.evidence !== "all") search.set("evidence", params.evidence);
  const query = search.toString();
  return query ? `${baseHref}?${query}` : baseHref;
}

function badgeTone(value?: string) {
  if (!value) return "neutral";
  if (["approved", "passed", "good", "verified"].includes(value)) return "success";
  if (["in_review", "warning", "partial", "partially_verified", "degraded"].includes(value)) return "warning";
  if (["failed", "poor", "rejected", "failure"].includes(value)) return "danger";
  return "neutral";
}

function labelFor(labels: LabelMap, type: string, id: string, fallback: string) {
  return labels[`${type}:${id}`] || fallback;
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

function objectChip(labels: LabelMap, type: string, id: string, fallback: string) {
  const href = objectHref(type, id);
  const label = labelFor(labels, type, id, fallback);
  const chip = <span className="font-medium">{label}</span>;
  return href ? <Link href={href} className="hover:text-accent hover:underline">{chip}</Link> : chip;
}

function describeSysMLRelation(relationType: string) {
  if (relationType === "satisfy") return "Satisfy";
  if (relationType === "verify") return "Verify";
  if (relationType === "deriveReqt") return "DeriveReqt";
  if (relationType === "contain") return "Contain";
  if (relationType === "refine") return "Refine";
  return relationType;
}
