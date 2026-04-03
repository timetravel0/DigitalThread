import Link from "next/link";
import { api } from "@/lib/api-client";
import { Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function BaselinePage({ params }: { params: { id: string } }) {
  const data = await api.baseline(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Baseline not found.</div>;
  return (
    <div className="space-y-6">
      <SectionTitle title={data.baseline.name} description={data.baseline.description} />
      <Card>
        <CardHeader><div className="font-semibold">Baseline items</div></CardHeader>
        <CardBody className="space-y-3">
          {data.items.map((item: any) => <div key={item.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{item.object_type} - {item.object_id}</div><div className="text-xs text-muted">Version {item.object_version}</div></div>)}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}


