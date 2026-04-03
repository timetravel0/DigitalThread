import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle, StatCard } from "@/components/ui";
import { SeedButton } from "@/components/seed-button";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let dashboard;
  let seedError: string | null = null;
  try {
    dashboard = await api.dashboard();
  } catch {
    dashboard = null;
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Dashboard"
        description="Projects, traceability, and evidence at a glance."
        action={<Button href="/projects">View projects</Button>}
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Total requirements" value={dashboard?.kpis.total_requirements ?? 0} />
        <StatCard label="Requirements with components" value={dashboard?.kpis.requirements_with_allocated_components ?? 0} />
        <StatCard label="Requirements at risk" value={dashboard?.kpis.requirements_at_risk ?? 0} sub="Failed linked tests in the last 30 days" />
        <StatCard label="Failed tests 30d" value={dashboard?.kpis.failed_tests_last_30_days ?? 0} />
        <StatCard label="Open change requests" value={dashboard?.kpis.open_change_requests ?? 0} />
        <Card>
          <CardBody>
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Seed data</div>
            <div className="mt-2 text-lg font-semibold">Drone inspection demo</div>
            <p className="mt-2 text-sm text-muted">If the API is empty, seed the inspection drone example to populate the UI.</p>
            <div className="mt-4">
              <SeedButton />
            </div>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="font-semibold">Projects</div>
              <Link href="/projects" className="text-sm text-accent">
                All projects
              </Link>
            </div>
          </CardHeader>
          <CardBody>
            {dashboard?.projects?.length ? (
              <div className="space-y-3">
                {dashboard.projects.map((project) => (
                  <Link key={project.id} href={`/projects/${project.id}`} className="block rounded-2xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-semibold">{project.code} - {project.name}</div>
                        <div className="mt-1 text-sm text-muted">{project.description}</div>
                      </div>
                      <Badge tone={project.status === "active" ? "success" : "neutral"}>{project.status}</Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No projects yet" description="Seed the demo project or create a new project from the projects page." action={<Button href="/projects">Go to projects</Button>} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <div className="font-semibold">Recent activity</div>
          </CardHeader>
          <CardBody className="space-y-4">
            {(dashboard?.recent_test_runs || []).slice(0, 5).map((run) => (
              <div key={run.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{run.summary}</div>
                  <Badge tone={run.result === "failed" ? "danger" : run.result === "passed" ? "success" : "warning"}>{run.result}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted">{run.execution_date}</div>
              </div>
            ))}
            {(dashboard?.recent_changes || []).slice(0, 3).map((change) => (
              <div key={change.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="text-sm font-medium">{change.key}</div>
                <div className="mt-1 text-xs text-muted">{change.title}</div>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

