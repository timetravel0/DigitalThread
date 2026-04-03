import { api } from "@/lib/api-client";
import { BlockForm } from "@/components/block-form";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

export default async function EditBlockPage({ params }: { params: { id: string } }) {
  const data = await api.block(params.id);
  if (data.block.status === "approved") {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader><div className="font-semibold">Approved block</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This block is approved and cannot be edited in place.</p>
            <p>Create a draft version, then open the draft for editing.</p>
            <div className="flex items-center gap-3">
              <Badge>{data.block.status}</Badge>
              <WorkflowActions kind="block" id={data.block.id} status={data.block.status} />
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }
  return <BlockForm initial={data.block} />;
}
