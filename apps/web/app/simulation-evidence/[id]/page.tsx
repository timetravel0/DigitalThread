import Link from "next/link";
import type { ReactNode } from "react";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";

export const dynamic = "force-dynamic";

export default async function SimulationEvidencePage({ params }: { params: { id: string } }) {
  const data = await api.simulationEvidenceDetail(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Simulation evidence not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.title}
        description="Simulation evidence is a first-class record distinct from generic verification evidence and test runs."
        action={<ButtonLink href={`/projects/${data.project_id}/simulation-evidence`}>Back to project evidence</ButtonLink>}
      />
      <SimulationEvidenceCard evidence={data} objectHref={objectHref} />
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
          }) : <div className="text-sm text-muted">No related objects linked yet.</div>}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  return null;
}

function ButtonLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link href={href} className="rounded-full border border-line px-3 py-1.5 text-sm text-text hover:bg-white/5">{children}</Link>;
}
