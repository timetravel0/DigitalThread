"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Badge, Card, CardBody, CardHeader, StatCard } from "@/components/ui";
import { VerificationStatusBreakdownCard } from "@/components/verification-status-breakdown";
import { getLabels, type LabelSet } from "@/lib/labels";
import type { Dashboard } from "@/lib/types";

export function DashboardViews({ dashboard, labels = getLabels("engineering") }: { dashboard: Dashboard | null; labels?: LabelSet }) {
  // TODO: resolve profile per-project when dashboard supports multi-project KPI breakdown.
  const [mode, setMode] = useState<"manager" | "engineering">("manager");
  const projects = dashboard && "projects" in dashboard ? dashboard.projects ?? [] : [];
  const managerCards = useMemo(
    () => [
      { label: `${labels.requirements} at risk`, value: dashboard?.kpis.requirements_at_risk ?? 0, sub: "Dashboard risk view" },
      { label: "Failed tests 30d", value: dashboard?.kpis.failed_tests_last_30_days ?? 0, sub: "Execution health" },
      { label: labels.kpi_open_changes, value: dashboard?.kpis.open_change_requests ?? 0, sub: "Change pipeline" },
    ],
    [dashboard, labels],
  );
  const engineeringCards = useMemo(
    () => [
      { label: labels.requirements, value: dashboard?.kpis.total_requirements ?? 0, sub: "Authoring scope" },
      { label: `${labels.requirements} with components`, value: dashboard?.kpis.requirements_with_allocated_components ?? 0, sub: "Allocation coverage" },
      { label: `${labels.requirements} with tests`, value: dashboard?.kpis.requirements_with_verifying_tests ?? 0, sub: "Verification coverage" },
    ],
    [dashboard, labels],
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardBody className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Dashboard view</div>
            <div className="mt-1 text-sm text-muted">Switch between a manager-oriented and engineering-oriented summary.</div>
          </div>
          <div className="flex rounded-full border border-line bg-panel2 p-1">
            <button className={`rounded-full px-3 py-1 text-sm ${mode === "manager" ? "bg-accent text-slate-950" : "text-muted"}`} onClick={() => setMode("manager")}>Manager</button>
            <button className={`rounded-full px-3 py-1 text-sm ${mode === "engineering" ? "bg-accent text-slate-950" : "text-muted"}`} onClick={() => setMode("engineering")}>Engineering</button>
          </div>
        </CardBody>
      </Card>

      {mode === "manager" ? (
        <div className="grid gap-4 md:grid-cols-3">
          {managerCards.map((card) => <StatCard key={card.label} label={card.label} value={card.value} sub={card.sub} />)}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {engineeringCards.map((card) => <StatCard key={card.label} label={card.label} value={card.value} sub={card.sub} />)}
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-3">
        <VerificationStatusBreakdownCard breakdown={dashboard?.verification_status_breakdown ?? { verified: 0, partially_verified: 0, at_risk: 0, failed: 0, not_covered: 0 }} />
        <Card className="xl:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="font-semibold">{mode === "manager" ? "Projects and decisions" : "Engineering activity"}</div>
              <Link href="/projects" className="text-sm text-accent">All projects</Link>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            {projects.map((project) => (
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
          </CardBody>
        </Card>
      </div>
    </div>
  );
}

