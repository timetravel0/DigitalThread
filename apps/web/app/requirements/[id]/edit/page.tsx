import { api } from "@/lib/api-client";
import { RequirementForm } from "@/components/requirement-form";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

export default async function EditRequirementPage({ params }: { params: { id: string } }) {
  const data = await api.requirement(params.id);
  if (data.requirement.status === "approved") {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader><div className="font-semibold">Approved requirement</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This requirement is approved and cannot be edited in place.</p>
            <p>Create a new draft version, then open the draft for editing.</p>
            <div className="flex items-center gap-3">
              <Badge>{data.requirement.status}</Badge>
              <WorkflowActions kind="requirement" id={data.requirement.id} status={data.requirement.status} />
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }
  return <RequirementForm initial={data.requirement} />;
}
