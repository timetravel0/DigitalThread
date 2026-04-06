"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader } from "@/components/ui";
import type { Dashboard, Project } from "@/lib/types";
import type { LabelSet } from "@/lib/labels";

type HealthDashboard = Dashboard | null;

function clampPct(value: number) {
  return Math.max(0, Math.min(100, value));
}

function pct(part: number, total: number) {
  if (!total) return 0;
  return clampPct(Math.round((part / total) * 100));
}

function Bar({
  label,
  value,
  total,
  danger = false,
}: {
  label: string;
  value: number;
  total: number;
  danger?: boolean;
}) {
  const percentage = pct(value, total);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-muted">{label}</span>
        <span className="text-text">{percentage}%</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/10">
        <div
          className={`h-1.5 rounded-full ${danger ? "bg-danger" : "bg-accent"}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export function ProjectHealthCard({
  dashboard,
  labels,
  projectId,
  project,
  counts,
}: {
  dashboard: HealthDashboard;
  labels: LabelSet;
  projectId: string;
  project: Pick<Project, "code" | "name" | "description" | "domain_profile">;
  counts: {
    requirements: number;
    blocks: number;
    tests: number;
    links: number;
    evidence: number;
    baselines: number;
    changeRequests: number;
  };
}) {
  const [resolvedDashboard, setResolvedDashboard] = useState<HealthDashboard>(dashboard);
  const [loading, setLoading] = useState(dashboard === null);
  const [error, setError] = useState(false);

  useEffect(() => {
    setResolvedDashboard(dashboard);
    setLoading(dashboard === null);
    setError(false);
  }, [dashboard]);

  useEffect(() => {
    if (dashboard !== null) return;
    let cancelled = false;
    setLoading(true);
    setError(false);
    api
      .projectDashboard(projectId)
      .then((next) => {
        if (cancelled) return;
        setResolvedDashboard(next);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(true);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [dashboard, projectId]);

  const kpis = useMemo(() => {
    const source = resolvedDashboard?.kpis;
    return {
      total_requirements: source?.total_requirements ?? 0,
      requirements_with_allocated_components: source?.requirements_with_allocated_components ?? 0,
      requirements_with_verifying_tests: source?.requirements_with_verifying_tests ?? 0,
      requirements_at_risk: source?.requirements_at_risk ?? 0,
      open_change_requests: source?.open_change_requests ?? 0,
    };
  }, [resolvedDashboard]);

  const profileText = project.domain_profile === "engineering"
    ? "Engineering profile"
    : project.domain_profile === "manufacturing"
      ? "Manufacturing profile"
      : project.domain_profile === "personal"
        ? "Personal profile"
        : "Custom profile";

  const total = kpis.total_requirements;
  const action = total === 0
    ? { href: `/projects/${projectId}/requirements`, label: `Start by adding your first ${labels.requirements}` }
    : kpis.requirements_with_allocated_components === 0
      ? { href: `/projects/${projectId}/blocks`, label: `Link ${labels.requirements} to ${labels.blocks}` }
      : kpis.requirements_with_verifying_tests === 0
        ? { href: `/projects/${projectId}/tests`, label: `Add ${labels.testCases} to verify your ${labels.requirements}` }
        : counts.evidence === 0
          ? { href: `/projects/${projectId}/requirements`, label: `Open a ${labels.requirement.toLowerCase()} and add the first evidence record` }
          : counts.baselines === 0
            ? { href: `/projects/${projectId}/baselines`, label: `Create a baseline when you want a review snapshot` }
            : kpis.open_change_requests > 0
              ? { href: `/projects/${projectId}/change-requests`, label: `${kpis.open_change_requests} open ${labels.changeRequests} pending review` }
              : { href: `/projects/${projectId}/graph`, label: `${labels.requirements} are connected and ready to review`, success: true };

  const quickActions = total === 0
    ? [
        { href: `/projects/${projectId}/requirements`, label: `Create ${labels.requirement}` },
        { href: `/projects/${projectId}/blocks`, label: `Create ${labels.block}` },
        { href: `/projects/${projectId}/tests`, label: `Create ${labels.testCase}` },
      ]
    : kpis.requirements_with_allocated_components === 0
      ? [
          { href: `/projects/${projectId}/blocks`, label: `Create ${labels.block}` },
          { href: `/projects/${projectId}/requirements`, label: `Review ${labels.requirements}` },
          { href: `/projects/${projectId}/graph`, label: "Open graph" },
        ]
      : kpis.requirements_with_verifying_tests === 0
        ? [
            { href: `/projects/${projectId}/tests`, label: `Create ${labels.testCase}` },
            { href: `/projects/${projectId}/requirements`, label: `Review ${labels.requirements}` },
            { href: `/projects/${projectId}/matrix`, label: "Open matrix" },
          ]
        : [
            { href: `/projects/${projectId}/graph`, label: "Open graph" },
            { href: `/projects/${projectId}/matrix`, label: "Open matrix" },
            { href: `/projects/${projectId}/baselines`, label: `Review ${labels.baselines}` },
          ];

  const recentRuns = (resolvedDashboard?.recent_test_runs || []).slice(0, 3);
  const recentChanges = (resolvedDashboard?.recent_changes || []).slice(0, 3);
  const recentLinks = (resolvedDashboard?.recent_links || []).slice(0, 3);
  const hasRecentActivity = recentRuns.length > 0 || recentChanges.length > 0 || recentLinks.length > 0;

  if (error) {
    return null;
  }

  if (loading && !resolvedDashboard) {
    return (
      <Card>
        <CardBody className="grid gap-4 md:grid-cols-2">
          <div className="space-y-4">
            <div className="h-4 w-32 skeleton rounded-full" />
            <div className="space-y-3">
              <div className="h-8 skeleton rounded-xl" />
              <div className="h-8 skeleton rounded-xl" />
              <div className="h-8 skeleton rounded-xl" />
            </div>
          </div>
          <div className="space-y-3">
            <div className="h-4 w-28 skeleton rounded-full" />
            <div className="h-16 skeleton rounded-2xl" />
            <div className="h-16 skeleton rounded-2xl" />
            <div className="h-16 skeleton rounded-2xl" />
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Project cockpit</div>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold text-text">
                {project.code} - {project.name}
              </h2>
              <Badge tone="accent">{profileText}</Badge>
            </div>
            <p className="mt-2 max-w-3xl text-sm text-muted">{project.description}</p>
          </div>
        </div>
      </CardHeader>
      <CardBody className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label={labels.requirements} value={counts.requirements} sub="Thread entry points" />
          <MetricCard label={labels.blocks} value={counts.blocks} sub="Realization objects" />
          <MetricCard label={labels.testCases} value={counts.tests} sub="Verification objects" />
          <MetricCard label="Links + evidence" value={counts.links + counts.evidence} sub="Thread connections and proof" />
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <div className="space-y-4">
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Thread status</div>
            <div className="grid gap-3 md:grid-cols-2">
              <StatusTile label={labels.requirements} value={counts.requirements} />
              <StatusTile label={labels.blocks} value={counts.blocks} />
              <StatusTile label={labels.testCases} value={counts.tests} />
              <StatusTile label="Links" value={counts.links} />
              <StatusTile label="Evidence" value={counts.evidence} />
              <StatusTile label={labels.baselines} value={counts.baselines} />
              <StatusTile label={labels.changeRequests} value={counts.changeRequests} />
            </div>
            <div className="space-y-4 rounded-2xl border border-line bg-panel2 p-4">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Coverage view</div>
              <Bar label="Allocation" value={kpis.requirements_with_allocated_components} total={total} />
              <Bar label="Verification" value={kpis.requirements_with_verifying_tests} total={total} />
              <Bar label="At risk" value={kpis.requirements_at_risk} total={total} danger={kpis.requirements_at_risk > 0} />
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Recommended next step</div>
            <div className="space-y-3 rounded-2xl border border-line bg-panel2 p-4">
              <div className="text-sm text-text">
                {action.success ? (
                  <span className="text-success">✓ {action.label}</span>
                ) : (
                  <span>{action.label}</span>
                )}
              </div>
              <p className="text-sm text-muted">
                {total === 0
                  ? `No ${labels.requirements.toLowerCase()} yet. Start the thread at the requirement layer.`
                  : kpis.requirements_with_allocated_components === 0
                    ? `The project has ${labels.requirements.toLowerCase()}, but nothing is linked to ${labels.blocks.toLowerCase()} yet.`
                    : kpis.requirements_with_verifying_tests === 0
                      ? `The thread is partially built. Add ${labels.testCases.toLowerCase()} so verification becomes visible.`
                      : counts.evidence === 0
                        ? `Verification is still thin. Open a ${labels.requirement.toLowerCase()} and add evidence from there.`
                        : counts.baselines === 0
                          ? `The thread is populated. Create a baseline when you need a review snapshot.`
                          : kpis.open_change_requests > 0
                            ? `There are open changes waiting for review.`
                            : `The core thread is populated. Use the graph or matrix to inspect it further.`}
              </p>
              <Link href={action.href} className="inline-flex text-sm font-medium text-accent hover:underline">
                Open relevant view
              </Link>
            </div>

            <div className="space-y-3">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Quick actions</div>
              <div className="grid gap-2 md:grid-cols-3">
                {quickActions.map((actionItem) => (
                  <Button key={actionItem.href} href={actionItem.href} variant="secondary" className="w-full">
                    {actionItem.label}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {hasRecentActivity ? (
          <div className="space-y-3">
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Recent activity</div>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2 rounded-2xl border border-line bg-panel2 p-4">
                <div className="text-sm font-medium">Recent test runs</div>
                {recentRuns.length ? (
                  recentRuns.map((run) => (
                    <Link key={run.id} href={`/test-cases/${run.test_case_id}`} className="block rounded-xl border border-line bg-background/50 p-3 hover:border-accent/50">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-medium">{run.summary}</div>
                        <Badge tone={run.result === "failed" ? "danger" : run.result === "passed" ? "success" : "warning"}>{run.result}</Badge>
                      </div>
                      <div className="mt-1 text-xs text-muted">{run.execution_date}</div>
                    </Link>
                  ))
                ) : (
                  <div className="text-sm text-muted">No recent test runs.</div>
                )}
              </div>

              <div className="space-y-2 rounded-2xl border border-line bg-panel2 p-4">
                <div className="text-sm font-medium">Recent changes</div>
                {recentChanges.length ? (
                  recentChanges.map((change) => (
                    <Link key={change.id} href={`/change-requests/${change.id}`} className="block rounded-xl border border-line bg-background/50 p-3 hover:border-accent/50">
                      <div className="text-sm font-medium">{change.key}</div>
                      <div className="mt-1 text-xs text-muted">{change.title}</div>
                    </Link>
                  ))
                ) : (
                  <div className="text-sm text-muted">No recent change requests.</div>
                )}
              </div>

              <div className="space-y-2 rounded-2xl border border-line bg-panel2 p-4">
                <div className="text-sm font-medium">Recent links</div>
                {recentLinks.length ? (
                  recentLinks.map((link) => (
                    <div key={link.id} className="rounded-xl border border-line bg-background/50 p-3">
                      <div className="text-sm font-medium">
                        {link.source_label || link.source_type} <span className="text-muted">→</span> {link.target_label || link.target_type}
                      </div>
                      <div className="mt-1 text-xs text-muted">
                        {link.relation_type}
                        {link.rationale ? ` · ${link.rationale}` : ""}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-muted">No recent links.</div>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function MetricCard({ label, value, sub }: { label: string; value: number; sub: string }) {
  return (
    <div className="rounded-2xl border border-line bg-panel2 p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-3xl font-semibold">{value}</div>
      <div className="mt-1 text-sm text-muted">{sub}</div>
    </div>
  );
}

function StatusTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 px-3 py-3">
      <div className="text-xs uppercase tracking-[0.18em] text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
