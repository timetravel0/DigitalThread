import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function BaselinePage({ params }: { params: { id: string } }) {
  const data = await api.baseline(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Baseline not found.</div>;
  const projectId = data.baseline.project_id;
  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.baseline.name}
        description={data.baseline.description || "Approved baseline snapshot"}
        action={
          <div className="flex flex-wrap gap-2">
            <Button href={`/projects/${projectId}/baselines`} variant="secondary">Back to baselines</Button>
            <Button href={`/projects/${projectId}/authoritative-sources?tab=configuration-contexts`} variant="secondary">Open configuration contexts</Button>
          </div>
        }
      />
      <Card>
        <CardHeader><div className="font-semibold">Baseline items</div></CardHeader>
        <CardBody className="space-y-3">
          {data.items.map((item: any) => (
            <div key={item.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="font-medium">{item.object_type} - {item.object_id}</div>
              <div className="text-xs text-muted">Version {item.object_version}</div>
            </div>
          ))}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Related configuration contexts</div></CardHeader>
        <CardBody className="space-y-3">
          <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
            This baseline is linked to configuration contexts that contain the same approved internal item set.
          </div>
          {data.related_configuration_contexts.length ? (
            data.related_configuration_contexts.map((context: any) => (
              <Link key={context.id} href={`/configuration-contexts/${context.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold">{context.key} - {context.name}</div>
                    <div className="mt-1 text-sm text-muted">{context.context_type}</div>
                  </div>
                  <Badge tone={context.status === "frozen" ? "accent" : context.status === "active" ? "success" : "neutral"}>{context.status}</Badge>
                </div>
              </Link>
            ))
          ) : (
            <EmptyState title="No matching configuration context" description="No configuration context in this project contains the same approved item set as this baseline." />
          )}
        </CardBody>
      </Card>
      <Link href={`/projects/${projectId}`} className="text-sm text-accent">Back to project workspace</Link>
    </div>
  );
}
