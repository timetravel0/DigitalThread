"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody } from "@/components/ui";
import type { Dashboard } from "@/lib/types";
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
}: {
  dashboard: HealthDashboard;
  labels: LabelSet;
  projectId: string;
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

  const total = kpis.total_requirements;
  const allocationPct = pct(kpis.requirements_with_allocated_components, total);
  const verificationPct = pct(kpis.requirements_with_verifying_tests, total);
  const riskPct = pct(kpis.requirements_at_risk, total);

  const action = total === 0
    ? { href: `/projects/${projectId}/requirements`, label: `Start by adding your first ${labels.requirements}` }
    : kpis.requirements_with_allocated_components === 0
      ? { href: `/projects/${projectId}/blocks`, label: `Link ${labels.requirements} to ${labels.blocks}` }
      : kpis.requirements_with_verifying_tests === 0
        ? { href: `/projects/${projectId}/tests`, label: `Add ${labels.testCases} to verify your ${labels.requirements}` }
        : kpis.open_change_requests > 0
          ? { href: `/projects/${projectId}/change-requests`, label: `${kpis.open_change_requests} open ${labels.changeRequests} pending review` }
          : { href: `/projects/${projectId}/requirements`, label: `${labels.requirements} are allocated and verified`, success: true };

  return (
    <Card>
      <CardBody className="grid gap-6 md:grid-cols-2">
        <div className="space-y-4">
          <div>
            <div className="text-xs uppercase tracking-[0.2em] text-muted">Project health</div>
            <div className="mt-1 text-sm text-muted">Coverage and verification health for the current project.</div>
          </div>
          <div className="space-y-4">
            <Bar label="Allocation" value={kpis.requirements_with_allocated_components} total={total} />
            <Bar label="Verification" value={kpis.requirements_with_verifying_tests} total={total} />
            <Bar label="At risk" value={kpis.requirements_at_risk} total={total} danger={kpis.requirements_at_risk > 0} />
          </div>
        </div>

        <div className="space-y-4">
          <div className="text-xs uppercase tracking-[0.2em] text-muted">Next action</div>
          <div className="space-y-3 rounded-2xl border border-line bg-panel2 p-4">
            <div className="text-sm text-text">
              {action.success ? (
                <span className="text-success">✓ {action.label}</span>
              ) : (
                <span>{action.label}</span>
              )}
            </div>
            <Link href={action.href} className="inline-flex text-sm font-medium text-accent hover:underline">
              Open relevant view
            </Link>
          </div>
          <div className="space-y-3">
            <MetricRow label={labels.requirements} value={total} />
            <MetricRow label={`${labels.requirements} with components`} value={kpis.requirements_with_allocated_components} />
            <MetricRow label={`${labels.requirements} with tests`} value={kpis.requirements_with_verifying_tests} />
            <MetricRow label={`${labels.requirements} at risk`} value={kpis.requirements_at_risk} />
            <MetricRow label={labels.kpi_open_changes} value={kpis.open_change_requests} />
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-background/40 px-3 py-2 text-sm">
      <span className="text-muted">{label}</span>
      <Badge tone="neutral">{value}</Badge>
    </div>
  );
}
