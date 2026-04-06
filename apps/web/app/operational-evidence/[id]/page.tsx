import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { OperationalEvidenceCard } from "@/components/operational-evidence-card";

export const dynamic = "force-dynamic";

export default async function OperationalEvidencePage({ params }: { params: { id: string } }) {
  const data = await api.operationalEvidenceDetail(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Operational evidence not found.</div>;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.title}
        description="Operational evidence is a batch-style field/telemetry record that complements verification evidence and does not replace operational runs."
        action={<Link href={`/projects/${data.project_id}/operational-evidence`} className="rounded-full border border-line px-3 py-1.5 text-sm text-text hover:bg-white/5">Back to project evidence</Link>}
      />
      <OperationalEvidenceCard evidence={data} objectHref={objectHref} />
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
          }) : <div className="text-sm text-muted">No related objects linked yet. Operational evidence belongs here when telemetry or batch observations need to stay connected to the requirement or verification record they support.</div>}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "operational_evidence") return `/operational-evidence/${objectId}`;
  return null;
}
