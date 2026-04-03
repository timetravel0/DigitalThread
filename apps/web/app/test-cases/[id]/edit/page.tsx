import { api } from "@/lib/api-client";
import { TestCaseForm } from "@/components/test-case-form";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

export default async function EditTestCasePage({ params }: { params: { id: string } }) {
  const data = await api.testCase(params.id);
  if (data.test_case.status === "approved") {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader><div className="font-semibold">Approved test case</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This test case is approved and cannot be edited in place.</p>
            <p>Create a draft version, then open the draft for editing.</p>
            <div className="flex items-center gap-3">
              <Badge>{data.test_case.status}</Badge>
              <WorkflowActions kind="test_case" id={data.test_case.id} status={data.test_case.status} />
            </div>
          </CardBody>
        </Card>
      </div>
    );
  }
  return <TestCaseForm initial={data.test_case} />;
}
