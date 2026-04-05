import { api } from "@/lib/api-client";
import { Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { SeedButton } from "@/components/seed-button";
import { DashboardViews } from "@/components/dashboard-views";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let dashboard;
  try {
    dashboard = await api.dashboard();
  } catch {
    dashboard = null;
  }
  // TODO: resolve profile per-project when dashboard supports multi-project KPI breakdown.

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Dashboard"
        description="Projects, traceability, and evidence at a glance."
        action={<Button href="/projects">View projects</Button>}
      />

      <DashboardViews dashboard={dashboard} />

      <div className="grid gap-6 xl:grid-cols-3">
        {[
          {
            profile: "engineering" as const,
            title: "Engineering demo",
            description: "Seed the drone inspection scenario with the full engineering workspace.",
          },
          {
            profile: "manufacturing" as const,
            title: "Manufacturing demo",
            description: "Seed a production-oriented demo with quality and conformance language.",
          },
          {
            profile: "personal" as const,
            title: "Personal demo",
            description: "Seed a lightweight personal project with goal and verification labels.",
          },
        ].map((card) => (
          <Card key={card.profile}>
            <CardHeader>
              <div className="font-semibold">{card.title}</div>
            </CardHeader>
            <CardBody>
              <p className="mt-2 text-sm text-muted">{card.description}</p>
              <div className="mt-4">
                <SeedButton profile={card.profile} />
              </div>
            </CardBody>
          </Card>
        ))}

        <Card>
          <CardHeader>
            <div className="font-semibold">Recent activity</div>
          </CardHeader>
          <CardBody className="space-y-4">
            {(dashboard?.recent_test_runs || []).slice(0, 5).map((run) => (
              <div key={run.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium">{run.summary}</div>
                  <span className={`rounded-full border px-2.5 py-1 text-xs font-medium ${run.result === "failed" ? "border-danger/30 bg-danger/15 text-danger" : run.result === "passed" ? "border-success/30 bg-success/15 text-success" : "border-yellow-400/30 bg-yellow-400/15 text-yellow-200"}`}>{run.result}</span>
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

      {!dashboard?.projects?.length ? (
        <EmptyState
          title="No projects yet"
          description="Seed the demo project or create a new project from the projects page."
          action={<Button href="/projects">Go to projects</Button>}
        />
      ) : null}
    </div>
  );
}
