import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { WorkflowActions } from "@/components/workflow-actions";

export const dynamic = "force-dynamic";

export default async function TestCasePage({ params }: { params: { id: string } }) {
  const data = await api.testCase(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Test case not found.</div>;
  return (
    <div className="space-y-6">
      <SectionTitle title={`${data.test_case.key} - ${data.test_case.title}`} description={data.test_case.description} />
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div className="font-semibold">Test case record</div>
            <div className="flex flex-wrap gap-2">
              {data.test_case.status === "approved" || data.test_case.status === "in_review" ? null : (
                <Button href={`/test-cases/${data.test_case.id}/edit`} variant="secondary">Edit</Button>
              )}
              <WorkflowActions kind="test_case" id={data.test_case.id} status={data.test_case.status} />
            </div>
          </div>
        </CardHeader>
        <CardBody className="space-y-3">
          <Row label="Method" value={data.test_case.method} />
          <Row label="Status" value={<Badge>{data.test_case.status}</Badge>} />
          <Row label="Version" value={data.test_case.version} />
        </CardBody>
      </Card>
      {data.test_case.status === "approved" ? (
        <Card>
          <CardHeader><div className="font-semibold">Approved item editing</div></CardHeader>
          <CardBody className="space-y-3 text-sm text-muted">
            <p>This test case is approved and cannot be edited in place.</p>
            <p>Create a new draft version before changing the test content.</p>
            <WorkflowActions kind="test_case" id={data.test_case.id} status={data.test_case.status} />
          </CardBody>
        </Card>
      ) : null}
      <Card>
        <CardHeader><div className="font-semibold">Runs</div></CardHeader>
        <CardBody className="space-y-3">
          {data.runs.map((run: any) => (
            <div key={run.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="flex items-center justify-between gap-4">
                <div className="font-medium">{run.summary}</div>
                <Badge tone={run.result === "failed" ? "danger" : run.result === "passed" ? "success" : "warning"}>{run.result}</Badge>
              </div>
              <div className="mt-1 text-xs text-muted">{run.execution_date}</div>
            </div>
          ))}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Traceability</div></CardHeader>
        <CardBody className="space-y-3">
          {data.links.map((link: any) => <div key={link.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="text-xs text-muted">{link.relation_type}</div></div>)}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">History</div></CardHeader>
        <CardBody className="space-y-3">
          {(data.history || []).map((entry: any) => <div key={entry.id} className="rounded-xl border border-line bg-panel2 p-3"><div className="font-medium">Version {entry.version}</div><div className="text-xs text-muted">{entry.change_summary || entry.changed_at}</div></div>)}
        </CardBody>
      </Card>
      <Link href="/projects" className="text-sm text-accent">Back to projects</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}
