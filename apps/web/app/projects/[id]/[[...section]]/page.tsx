import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

const tabs = [
  { slug: "", label: "Overview" },
  { slug: "requirements", label: "Requirements" },
  { slug: "components", label: "Components" },
  { slug: "tests", label: "Tests" },
  { slug: "runs", label: "Operational Runs" },
  { slug: "links", label: "Links" },
  { slug: "matrix", label: "Matrix" },
  { slug: "baselines", label: "Baselines" },
  { slug: "change-requests", label: "Change Requests" },
];

function Tabs({ projectId, section }: { projectId: string; section: string }) {
  return (
    <div className="flex flex-wrap gap-2">
      {tabs.map((tab) => {
        const active = (tab.slug || "") === (section || "");
        const href = tab.slug ? `/projects/${projectId}/${tab.slug}` : `/projects/${projectId}`;
        return (
          <Link key={tab.label} href={href} className={`rounded-full border px-3 py-1.5 text-sm ${active ? "border-accent bg-accent/10 text-accent" : "border-line text-text hover:bg-white/5"}`}>
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}

export default async function ProjectWorkspace({ params }: { params: { id: string; section?: string[] } }) {
  const projectId = params.id;
  const section = params.section?.[0] ?? "";
  const [project, dashboard, requirements, components, tests, runs, links, baselines, changeRequests] = await Promise.all([
    api.project(projectId).catch(() => null),
    api.projectDashboard(projectId).catch(() => null),
    api.requirements(projectId).catch(() => []),
    api.components(projectId).catch(() => []),
    api.testCases(projectId).catch(() => []),
    api.operationalRuns(projectId).catch(() => []),
    api.links(projectId).catch(() => []),
    api.baselines(projectId).catch(() => []),
    api.changeRequests(projectId).catch(() => []),
  ]);

  if (!project) {
    return <EmptyState title="Project not found" description="The project may have been removed or the API is not available." />;
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${project.code} - ${project.name}`}
        description={project.description}
        action={<Button href={`/projects/${project.id}/matrix`}>Open matrix</Button>}
      />
      <Tabs projectId={project.id} section={section} />

      {section === "requirements" ? (
        <Card><CardHeader><div className="font-semibold">Requirements</div></CardHeader><CardBody><List items={requirements} kind="requirement" /></CardBody></Card>
      ) : section === "components" ? (
        <Card><CardHeader><div className="font-semibold">Components</div></CardHeader><CardBody><List items={components} kind="component" /></CardBody></Card>
      ) : section === "tests" ? (
        <Card><CardHeader><div className="font-semibold">Test Cases</div></CardHeader><CardBody><List items={tests} kind="test_case" /></CardBody></Card>
      ) : section === "runs" ? (
        <Card><CardHeader><div className="font-semibold">Operational Runs</div></CardHeader><CardBody>{runs.length ? runs.map((run: any) => <div key={run.id} className="mb-3 rounded-xl border border-line bg-panel2 p-4"><div className="font-semibold">{run.key}</div><div className="mt-1 text-sm text-muted">{run.date} - {run.duration_minutes} min - {run.outcome}</div><div className="mt-2 text-sm">{run.notes}</div></div>) : <EmptyState title="No operational runs yet" description="Seed data or add a new field run." />}</CardBody></Card>
      ) : section === "links" ? (
        <Card><CardHeader><div className="font-semibold">Traceability Links</div></CardHeader><CardBody>{links.length ? links.map((link: any) => <div key={link.id} className="mb-3 rounded-xl border border-line bg-panel2 p-4"><div className="font-semibold">{link.source_label || link.source_type} <span className="text-muted">-&gt;</span> {link.target_label || link.target_type}</div><div className="mt-1 text-sm text-muted">{link.relation_type}{link.rationale ? ` - ${link.rationale}` : ""}</div></div>) : <EmptyState title="No links yet" description="Create traceability relationships to populate the matrix." />}</CardBody></Card>
      ) : section === "matrix" ? (
        <Card><CardHeader><div className="font-semibold">Matrix</div></CardHeader><CardBody><div className="space-y-3"><div className="text-sm text-muted">Open the dedicated matrix view for a richer interactive grid.</div><Button href={`/projects/${project.id}/matrix`}>Go to matrix</Button></div></CardBody></Card>
      ) : section === "baselines" ? (
        <Card><CardHeader><div className="font-semibold">Baselines</div></CardHeader><CardBody>{baselines.length ? baselines.map((baseline: any) => <Link key={baseline.id} href={`/baselines/${baseline.id}`} className="mb-3 block rounded-xl border border-line bg-panel2 p-4"><div className="font-semibold">{baseline.name}</div><div className="mt-1 text-sm text-muted">{baseline.description}</div></Link>) : <EmptyState title="No baselines yet" description="Create a baseline from the current project state." />}</CardBody></Card>
      ) : section === "change-requests" ? (
        <Card><CardHeader><div className="font-semibold">Change Requests</div></CardHeader><CardBody>{changeRequests.length ? changeRequests.map((cr: any) => <Link key={cr.id} href={`/change-requests/${cr.id}`} className="mb-3 block rounded-xl border border-line bg-panel2 p-4"><div className="flex items-center justify-between gap-4"><div><div className="font-semibold">{cr.key} - {cr.title}</div><div className="mt-1 text-sm text-muted">{cr.description}</div></div><Badge tone={cr.status === "open" ? "warning" : "neutral"}>{cr.status}</Badge></div></Link>) : <EmptyState title="No change requests yet" description="Capture proposed changes and their impacts." />}</CardBody></Card>
      ) : (
        <div className="grid gap-6 xl:grid-cols-3">
          <Card className="xl:col-span-2">
            <CardHeader><div className="font-semibold">Project overview</div></CardHeader>
            <CardBody>
              <div className="grid gap-4 md:grid-cols-2">
                <Mini metric="Requirements" value={requirements.length} />
                <Mini metric="Components" value={components.length} />
                <Mini metric="Test cases" value={tests.length} />
                <Mini metric="Operational runs" value={runs.length} />
              </div>
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                <Mini metric="Allocated requirements" value={dashboard?.kpis.requirements_with_allocated_components ?? 0} />
                <Mini metric="Verified requirements" value={dashboard?.kpis.requirements_with_verifying_tests ?? 0} />
                <Mini metric="Requirements at risk" value={dashboard?.kpis.requirements_at_risk ?? 0} />
                <Mini metric="Open change requests" value={dashboard?.kpis.open_change_requests ?? 0} />
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardHeader><div className="font-semibold">Quick links</div></CardHeader>
            <CardBody className="space-y-3">
              <Button href={`/projects/${project.id}/requirements`} className="w-full">Requirements</Button>
              <Button href={`/projects/${project.id}/components`} className="w-full" variant="secondary">Components</Button>
              <Button href={`/projects/${project.id}/tests`} className="w-full" variant="secondary">Tests</Button>
              <Button href={`/projects/${project.id}/matrix`} className="w-full" variant="secondary">Matrix</Button>
            </CardBody>
          </Card>
        </div>
      )}
    </div>
  );
}

function Mini({ metric, value }: { metric: string; value: number }) {
  return (
    <div className="rounded-2xl border border-line bg-panel2 p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{metric}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function List({ items, kind }: { items: any[]; kind: "requirement" | "component" | "test_case" }) {
  if (!items.length) {
    return <EmptyState title="No items yet" description="Seed the demo project or create a new item." />;
  }
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <Link key={item.id} href={`/${kind === "test_case" ? "test-cases" : `${kind}s`}/${item.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="font-semibold">{item.key} - {item.title || item.name}</div>
              <div className="mt-1 text-sm text-muted">{item.description}</div>
            </div>
            <Badge tone={item.status === "failed" ? "danger" : item.status === "verified" || item.status === "passed" || item.status === "validated" ? "success" : "neutral"}>{item.status}</Badge>
          </div>
        </Link>
      ))}
    </div>
  );
}


