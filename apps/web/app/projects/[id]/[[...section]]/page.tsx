import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";

export const dynamic = "force-dynamic";

const tabs = [
  { slug: "", label: "Overview" },
  { slug: "requirements", label: "Requirements" },
  { slug: "blocks", label: "Blocks" },
  { slug: "tests", label: "Tests" },
  { slug: "runs", label: "Operational Runs" },
  { slug: "links", label: "Traceability" },
  { slug: "sysml", label: "SysML" },
  { slug: "review-queue", label: "Review Queue" },
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
        return <Link key={tab.label} href={href} className={`rounded-full border px-3 py-1.5 text-sm ${active ? "border-accent bg-accent/10 text-accent" : "border-line text-text hover:bg-white/5"}`}>{tab.label}</Link>;
      })}
    </div>
  );
}

const sysmlViews = [
  { key: "block-structure", label: "Block Structure" },
  { key: "satisfaction", label: "Satisfaction" },
  { key: "verification", label: "Verification" },
  { key: "derivations", label: "Derivations" },
];

export default async function ProjectWorkspace({ params, searchParams }: { params: { id: string; section?: string[] }; searchParams?: { view?: string } }) {
  const projectId = params.id;
  const section = params.section?.[0] ?? "";
  const view = searchParams?.view || "block-structure";
  const [project, dashboard, requirements, blocks, tests, runs, links, baselines, changeRequests, reviewQueue] = await Promise.all([
    api.project(projectId).catch(() => null),
    api.projectDashboard(projectId).catch(() => null),
    api.requirements(projectId).catch(() => []),
    api.blocks(projectId).catch(() => []),
    api.testCases(projectId).catch(() => []),
    api.operationalRuns(projectId).catch(() => []),
    api.links(projectId).catch(() => []),
    api.baselines(projectId).catch(() => []),
    api.changeRequests(projectId).catch(() => []),
    api.reviewQueue(projectId).catch(() => null),
  ]);

  if (!project) return <EmptyState title="Project not found" description="The project may have been removed or the API is not available." />;

  if (section === "sysml") {
    const tree = await api.sysmlTree(project.id).catch(() => null);
    const satisfaction = await api.sysmlSatisfaction(project.id).catch(() => null);
    const verification = await api.sysmlVerification(project.id).catch(() => null);
    const derivations = await api.sysmlDerivations(project.id).catch(() => null);
    return (
      <div className="space-y-6">
        <SectionTitle title={`${project.code} - ${project.name}`} description="SysML-inspired practice views for blocks, satisfaction, verification, and derivation." />
        <Tabs projectId={project.id} section={section} />
        <div className="flex flex-wrap gap-2">
          {sysmlViews.map((item) => <Button key={item.key} href={`/projects/${project.id}/sysml?view=${item.key}`} variant={view === item.key ? "primary" : "secondary"}>{item.label}</Button>)}
        </div>
        {view === "satisfaction" ? (
          <Card><CardHeader><div className="font-semibold">Satisfaction</div></CardHeader><CardBody><ObjectList items={(satisfaction?.rows || []).flatMap((row) => row.requirements.map((req) => ({ label: `${row.block.key} satisfies ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : view === "verification" ? (
          <Card><CardHeader><div className="font-semibold">Verification</div></CardHeader><CardBody><ObjectList items={(verification?.rows || []).flatMap((row) => row.requirements.map((req) => ({ label: `${row.test_case.key} verifies ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : view === "derivations" ? (
          <Card><CardHeader><div className="font-semibold">Derivations</div></CardHeader><CardBody><ObjectList items={(derivations?.rows || []).flatMap((row) => row.derived_requirements.map((req) => ({ label: `${row.source_requirement.key} derived from ${req.code || req.label}`, object_type: "requirement" })))} /></CardBody></Card>
        ) : (
          <Card>
            <CardHeader><div className="font-semibold">Block structure</div></CardHeader>
            <CardBody className="space-y-3">
              <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
                The seeded drone project demonstrates the SysML <span className="text-text">contains</span> relationship with a top-level <span className="text-text">Drone System</span> block and its subsystems.
              </div>
              <BlockTree nodes={tree?.roots || []} />
            </CardBody>
          </Card>
        )}
      </div>
    );
  }

  if (section === "review-queue") {
    return <SimpleListPage project={project} section={section} title="Review Queue" description="Items waiting in review." items={(reviewQueue?.items || []).map((item) => ({ key: item.key, label: `${item.object_type}: ${item.title}`, status: item.status, href: `/${item.object_type === "test_case" ? "test-cases" : item.object_type === "block" ? "blocks" : "requirements"}/${item.id}` }))} />;
  }

  if (section === "requirements") return <SimpleListPage project={project} section={section} title="Requirements" description="Editable requirements with approval workflow." items={requirements.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/requirements/${item.id}` }))} createHref={`/requirements/new?project=${project.id}`} />;
  if (section === "blocks") return <SimpleListPage project={project} section={section} title="Blocks" description="SysML-inspired structural elements." items={blocks.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.name}`, status: item.status, href: `/blocks/${item.id}` }))} createHref={`/blocks/new?project=${project.id}`} />;
  if (section === "tests") return <SimpleListPage project={project} section={section} title="Test Cases" description="Verification artifacts with workflow and history." items={tests.map((item: any) => ({ key: item.key, label: `${item.key} - ${item.title}`, status: item.status, href: `/test-cases/${item.id}` }))} createHref={`/test-cases/new?project=${project.id}`} />;
  if (section === "runs") return <SimpleListPage project={project} section={section} title="Operational Runs" description="Field evidence and telemetry." items={runs.map((run: any) => ({ key: run.key, label: `${run.key} - ${run.notes}`, status: run.outcome, href: "#" }))} />;
  if (section === "links") return <SimpleListPage project={project} section={section} title="Traceability Links" description="Manual traceability and SysML relations support." items={links.map((link: any) => ({ key: link.id, label: `${link.source_label || link.source_type} -> ${link.target_label || link.target_type}`, status: link.relation_type, href: "#" }))} />;
  if (section === "baselines") return <SimpleListPage project={project} section={section} title="Baselines" description="Approved-only snapshots by default." items={baselines.map((baseline: any) => ({ key: baseline.id, label: baseline.name, status: baseline.status, href: `/baselines/${baseline.id}` }))} />;
  if (section === "change-requests") return <SimpleListPage project={project} section={section} title="Change Requests" description="Impact-driven change management." items={changeRequests.map((cr: any) => ({ key: cr.key, label: `${cr.key} - ${cr.title}`, status: cr.status, href: `/change-requests/${cr.id}` }))} />;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${project.code} - ${project.name}`}
        description={project.description}
        action={
          <div className="flex flex-wrap gap-2">
            <Button href={`/projects/${project.id}/matrix`}>Open matrix</Button>
            <Button href={api.exportProjectUrl(project.id)} variant="secondary">Export JSON</Button>
          </div>
        }
      />
      <Tabs projectId={project.id} section={section} />
      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader><div className="font-semibold">Project overview</div></CardHeader>
          <CardBody>
            <div className="grid gap-4 md:grid-cols-2">
              <Mini metric="Requirements" value={requirements.length} />
              <Mini metric="Blocks" value={blocks.length} />
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
            <Button href={`/projects/${project.id}/blocks`} className="w-full" variant="secondary">Blocks</Button>
            <Button href={`/projects/${project.id}/tests`} className="w-full" variant="secondary">Tests</Button>
            <Button href={`/projects/${project.id}/sysml`} className="w-full" variant="secondary">SysML</Button>
            <Button href={`/projects/${project.id}/review-queue`} className="w-full" variant="secondary">Review Queue</Button>
            <Button href={api.exportProjectUrl(project.id)} className="w-full" variant="secondary">Export project bundle</Button>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

function SimpleListPage({ project, section, title, description, items, createHref }: { project: any; section: string; title: string; description: string; items: { key: string; label: string; status?: string; href: string }[]; createHref?: string }) {
  return (
    <div className="space-y-6">
      <SectionTitle title={`${project.code} - ${title}`} description={description} action={createHref ? <Button href={createHref}>Create</Button> : undefined} />
      <Tabs projectId={project.id} section={section} />
      <Card>
        <CardHeader><div className="font-semibold">{title}</div></CardHeader>
        <CardBody>{items.length ? <div className="space-y-3">{items.map((item) => <Link key={item.key} href={item.href} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50"><div className="flex items-center justify-between gap-4"><div><div className="font-semibold">{item.label}</div></div><Badge tone={item.status === "approved" ? "success" : item.status === "in_review" ? "warning" : item.status === "failed" ? "danger" : "neutral"}>{item.status || "item"}</Badge></div></Link>)}</div> : <EmptyState title={`No ${title.toLowerCase()} yet`} description={description} action={createHref ? <Button href={createHref}>Create first item</Button> : undefined} />}</CardBody>
      </Card>
    </div>
  );
}

function ObjectList({ items }: { items: { label: string; object_type: string }[] }) {
  return <div className="space-y-2">{items.map((item, index) => <div key={`${item.label}-${index}`} className="rounded-xl border border-line bg-panel2 p-3 text-sm">{item.label}</div>)}</div>;
}

function BlockTree({ nodes, depth = 0 }: { nodes: any[]; depth?: number }) {
  return (
    <div className="space-y-3">
      {nodes.map((node) => (
        <div key={node.block.id} className="rounded-xl border border-line bg-panel2 p-3" style={{ marginLeft: depth * 16 }}>
          <div className="font-semibold">{node.block.key} - {node.block.name}</div>
          <div className="text-xs text-muted">{node.block.block_kind} / {node.block.abstraction_level} / {node.block.status}</div>
          {node.satisfied_requirements?.length ? <div className="mt-2 text-xs text-muted">Satisfies {node.satisfied_requirements.length} requirements</div> : null}
          {node.linked_tests?.length ? <div className="mt-1 text-xs text-muted">Verified by {node.linked_tests.length} tests</div> : null}
          {node.children?.length ? <div className="mt-3 border-l border-line pl-4"><BlockTree nodes={node.children} depth={depth + 1} /></div> : null}
        </div>
      ))}
    </div>
  );
}

function Mini({ metric, value }: { metric: string; value: number }) {
  return <div className="rounded-2xl border border-line bg-panel2 p-4"><div className="text-xs uppercase tracking-[0.2em] text-muted">{metric}</div><div className="mt-2 text-2xl font-semibold">{value}</div></div>;
}
