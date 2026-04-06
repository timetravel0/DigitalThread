"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import { api } from "@/lib/api-client";
import type { Requirement, RequirementDetail, RequirementVerificationStatus } from "@/lib/types";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, Select } from "@/components/ui";

type ValidationProfile = "mission" | "power" | "thermal" | "evidence" | "release";

type ValidationAlert = {
  tone: "neutral" | "success" | "warning" | "danger" | "accent";
  title: string;
  description: string;
  links?: { label: string; href: string }[];
};

const PROFILES: { value: ValidationProfile; label: string; description: string }[] = [
  { value: "mission", label: "Mission check", description: "A broad review for the mission-level flow." },
  { value: "power", label: "Power check", description: "Highlights battery and power-related thresholds." },
  { value: "thermal", label: "Thermal check", description: "Highlights temperature and environment thresholds." },
  { value: "evidence", label: "Evidence check", description: "Focuses on evidence coverage and gaps." },
  { value: "release", label: "Release gate", description: "Highlights release flags and change-control warnings." },
];

export function ValidationWorkbench({
  projectId,
  projectCode,
  projectName,
  requirements,
}: {
  projectId: string;
  projectCode: string;
  projectName: string;
  requirements: Requirement[];
}) {
  const defaultRequirementId = useMemo(() => {
    const withCriteria = requirements.find((item) => Object.keys(item.verification_criteria_json || {}).length > 0);
    const approved = requirements.find((item) => item.status === "approved");
    return (withCriteria || approved || requirements[0])?.id || "";
  }, [requirements]);

  const [selectedRequirementId, setSelectedRequirementId] = useState(defaultRequirementId);
  const [profile, setProfile] = useState<ValidationProfile>("mission");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    detail: RequirementDetail;
    alerts: ValidationAlert[];
    validatedAt: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectedRequirement = useMemo(
    () => requirements.find((item) => item.id === selectedRequirementId) || null,
    [requirements, selectedRequirementId]
  );

  if (!requirements.length) {
    return (
      <EmptyState
        title="No requirements to validate yet"
        description={`Validation works when there is at least one requirement or goal to check. Create the first requirement, add measurable criteria, then come back here to run a guided validation for ${projectName}.`}
        action={<Button href={`/projects/${projectId}/requirements`}>Create requirement</Button>}
      />
    );
  }

  async function startValidation() {
    if (!selectedRequirementId) {
      setError("Select a requirement before starting validation.");
      setResult(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const detail = await api.requirement(selectedRequirementId);
      setResult({
        detail,
        alerts: buildAlerts(detail, profile),
        validatedAt: new Date().toISOString(),
      });
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Validation failed.");
    } finally {
      setLoading(false);
    }
  }

  function resetValidation() {
    setResult(null);
    setError(null);
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="font-semibold">Validation cockpit</div>
              <div className="mt-1 text-sm text-muted">
                A SidSat-style validation panel for non-technical reviewers. Select a requirement, choose a focus, then run the check inside {projectName}.
              </div>
            </div>
            <Badge tone="accent">Project {projectCode}</Badge>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.2em] text-muted">Target requirement</label>
              <Select value={selectedRequirementId} onChange={(event) => setSelectedRequirementId(event.target.value)}>
                {requirements.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.key} - {item.title}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-[0.2em] text-muted">Validation focus</label>
              <Select value={profile} onChange={(event) => setProfile(event.target.value as ValidationProfile)}>
                {PROFILES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button onClick={startValidation} disabled={loading || !selectedRequirementId}>
              {loading ? "Running..." : "Start Validation"}
            </Button>
            <Button onClick={resetValidation} variant="secondary" disabled={loading}>
              Clear results
            </Button>
          </div>

          <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
            {selectedRequirement
              ? `Selected requirement: ${selectedRequirement.key} - ${selectedRequirement.title}`
              : "Pick a requirement and press Start Validation to generate immediate alerts."}
          </div>
        </CardBody>
      </Card>

      {error ? (
        <Card>
          <CardHeader>
            <div className="font-semibold">Validation error</div>
          </CardHeader>
          <CardBody>
            <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">{error}</div>
          </CardBody>
        </Card>
      ) : null}

      {result ? (
        <div className="grid gap-6 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="font-semibold">Validation summary</div>
                <Badge tone={result.detail.verification_evaluation.status === "verified" ? "success" : result.detail.verification_evaluation.status === "failed" || result.detail.verification_evaluation.status === "not_covered" ? "danger" : "warning"}>
                  {humanizeStatus(result.detail.verification_evaluation.status)}
                </Badge>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              <SummaryRow label="Requirement" value={`${result.detail.requirement.key} - ${result.detail.requirement.title}`} />
              <SummaryRow label="Approval status" value={<Badge tone={approvalTone(result.detail.requirement.status)}>{result.detail.requirement.status}</Badge>} />
              <SummaryRow label="Verification status" value={<Badge tone={verificationTone(result.detail.verification_evaluation.status)}>{humanizeStatus(result.detail.verification_evaluation.status)}</Badge>} />
              <SummaryRow label="Validation focus" value={<Badge tone="accent">{labelForProfile(profile)}</Badge>} />
              <SummaryRow label="Decision source" value={humanizeDecisionSource(result.detail.verification_evaluation.decision_source)} />
              <SummaryRow label="Validated at" value={formatTimestamp(result.validatedAt)} />
              <SummaryRow label="Simulation evidence" value={result.detail.simulation_evidence.length} />
              <SummaryRow label="Operational evidence" value={result.detail.operational_evidence.length} />
              <SummaryRow label="Verification evidence" value={result.detail.verification_evidence.length} />
              <SummaryRow label="Released baselines" value={result.detail.impact.related_baselines.filter((baseline) => baseline.release_flag).length} />
              <SummaryRow label="Open change requests" value={result.detail.impact.open_change_requests.length} />
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <div className="font-semibold">Immediate alerts</div>
            </CardHeader>
            <CardBody className="space-y-3">
              {result.alerts.length ? (
                result.alerts.map((alert) => (
                  <div key={`${alert.title}-${alert.description}`} className="rounded-xl border border-line bg-panel2 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="font-medium text-text">{alert.title}</div>
                        <div className="mt-1 text-sm text-muted">{alert.description}</div>
                      </div>
                      <Badge tone={alert.tone}>{alert.tone}</Badge>
                    </div>
                    {alert.links?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {alert.links.map((link) => (
                          <Link key={link.href} href={link.href} className="rounded-full border border-line bg-background px-2.5 py-1 text-xs text-text hover:border-accent/60">
                            {link.label}
                          </Link>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <EmptyState title="No alerts generated" description="Start validation to analyze thresholds, evidence coverage, and release gates." />
              )}
            </CardBody>
          </Card>
        </div>
      ) : (
        <EmptyState
          title="Ready to validate"
          description="Use the dropdowns above to choose a requirement and a validation focus, then press Start Validation. The panel will show immediate alerts based on thresholds, evidence, and release gates."
        />
      )}

      {result ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="font-semibold">Threshold checks</div>
              <Badge tone="neutral">Detected from verification criteria</Badge>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {thresholdRows(result.detail).length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {thresholdRows(result.detail).map((row) => (
                  <div key={`${row.metric}-${row.rule}`} className="rounded-xl border border-line bg-panel2 p-4">
                    <div className="font-medium text-text">{row.label}</div>
                    <div className="mt-1 text-sm text-muted">{row.rule}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No thresholds defined"
                description="Add telemetry thresholds in the requirement form to make the validation cockpit produce deterministic alerts."
              />
            )}
            {result.detail.impact.related_baselines.filter((baseline) => baseline.release_flag).length ? (
              <div className="rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">
                Released baselines are linked to this requirement. Any change should go through a change request first.
              </div>
            ) : null}
            {result.detail.impact.open_change_requests.length ? (
              <div className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">
                Open change requests already affect this requirement. Review them before changing the design.
              </div>
            ) : null}
          </CardBody>
        </Card>
      ) : null}
    </div>
  );
}

function buildAlerts(detail: RequirementDetail, profile: ValidationProfile): ValidationAlert[] {
  const alerts: ValidationAlert[] = [];
  const criteria = detail.requirement.verification_criteria_json || {};
  const thresholds = thresholdRows(detail);
  const releasedBaselines = detail.impact.related_baselines.filter((baseline) => baseline.release_flag);
  const verificationStatus = detail.verification_evaluation.status;

  if (profile === "release") {
    if (releasedBaselines.length) {
      alerts.push({
        tone: "danger",
        title: "Alert: Release gate active",
        description: `This requirement is part of ${releasedBaselines.length} released baseline(s). Any modification should create a change request.`,
        links: releasedBaselines.map((baseline) => ({ label: baseline.name, href: `/baselines/${baseline.id}` })),
      });
    } else {
      alerts.push({
        tone: "success",
        title: "Release gate clear",
        description: "No released baseline currently locks this requirement.",
      });
    }
  }

  if (!thresholds.length && Object.keys(criteria).length === 0) {
    alerts.push({
      tone: "warning",
      title: "Alert: Add thresholds",
      description: "No verification criteria are defined yet. Add measurable thresholds to make the cockpit deterministic.",
    });
  }

  if (thresholds.length) {
    const ordered = thresholds
      .slice()
      .sort((left, right) => thresholdPriority(right.metric, profile) - thresholdPriority(left.metric, profile))
      .slice(0, 4);
    ordered.forEach((row) => {
      alerts.push({
        tone: "warning",
        title: `Alert: Check ${row.label}`,
        description: row.rule,
      });
    });
  }

  if (verificationStatus === "failed") {
    alerts.unshift({
      tone: "danger",
      title: "Alert: Requirement is violated",
      description: detail.verification_evaluation.decision_summary || "The computed verification state is failed.",
    });
  } else if (verificationStatus === "at_risk") {
    alerts.unshift({
      tone: "warning",
      title: "Alert: Requirement is at risk",
      description: detail.verification_evaluation.decision_summary || "The computed verification state indicates risk.",
    });
  } else if (verificationStatus === "partially_verified") {
    alerts.unshift({
      tone: "warning",
      title: "Alert: Validation is partial",
      description: detail.verification_evaluation.decision_summary || "Coverage is incomplete or mixed.",
    });
  } else if (verificationStatus === "verified") {
    alerts.unshift({
      tone: "success",
      title: "Validation passed",
      description: detail.verification_evaluation.decision_summary || "The requirement is currently verified.",
    });
  } else {
    alerts.unshift({
      tone: "danger",
      title: "Alert: Requirement is not covered",
      description: detail.verification_evaluation.decision_summary || "No linked evidence currently covers the requirement.",
    });
  }

  if (detail.verification_evidence.length) {
    alerts.push({
      tone: "accent",
      title: "Verification evidence found",
      description: `${detail.verification_evidence.length} verification evidence record(s) are linked to this requirement.`,
    });
  }

  if (detail.simulation_evidence.length) {
    alerts.push({
      tone: "accent",
      title: "Simulation evidence available",
      description: `${detail.simulation_evidence.length} simulation evidence record(s) are linked to this requirement.`,
    });
  }

  if (detail.operational_evidence.length) {
    alerts.push({
      tone: "accent",
      title: "Operational evidence available",
      description: `${detail.operational_evidence.length} operational evidence batch(es) are linked to this requirement.`,
    });
  }

  if (detail.impact.open_change_requests.length) {
    alerts.push({
      tone: "danger",
      title: "Change requests need review",
      description: `${detail.impact.open_change_requests.length} open change request(s) affect this requirement.`,
      links: detail.impact.open_change_requests.map((cr) => ({ label: cr.key, href: `/change-requests/${cr.id}` })),
    });
  }

  return dedupeAlerts(alerts);
}

function thresholdRows(detail: RequirementDetail) {
  const criteria = detail.requirement.verification_criteria_json || {};
  const thresholds = (criteria.telemetry_thresholds || criteria.thresholds || {}) as Record<string, any>;
  return Object.entries(thresholds)
    .filter(([, rule]) => rule && typeof rule === "object")
    .map(([metric, rule]) => {
      const parts: string[] = [];
      if (rule.min != null) parts.push(`min ${rule.min}`);
      if (rule.max != null) parts.push(`max ${rule.max}`);
      if (rule.equals != null) parts.push(`equals ${rule.equals}`);
      if (!parts.length) parts.push("threshold defined");
      return {
        metric,
        label: labelForMetric(metric),
        rule: `${metric}: ${parts.join(", ")}`,
      };
    });
}

function labelForMetric(metric: string) {
  const lower = metric.toLowerCase();
  if (lower.includes("battery") || lower.includes("power") || lower.includes("voltage") || lower.includes("current")) return "Check Power";
  if (lower.includes("temp") || lower.includes("thermal") || lower.includes("heat")) return "Check Thermal";
  if (lower.includes("duration") || lower.includes("endurance") || lower.includes("flight") || lower.includes("range")) return "Check Endurance";
  return `Check ${metric.replaceAll("_", " ")}`;
}

function thresholdPriority(metric: string, profile: ValidationProfile) {
  const lower = metric.toLowerCase();
  if (profile === "power" && (lower.includes("battery") || lower.includes("power") || lower.includes("voltage") || lower.includes("current"))) return 3;
  if (profile === "thermal" && (lower.includes("temp") || lower.includes("thermal") || lower.includes("heat"))) return 3;
  if (profile === "mission" && (lower.includes("duration") || lower.includes("endurance") || lower.includes("flight") || lower.includes("range"))) return 3;
  if (profile === "evidence") return 2;
  return 1;
}

function dedupeAlerts(alerts: ValidationAlert[]) {
  const seen = new Set<string>();
  return alerts.filter((alert) => {
    const key = `${alert.title}::${alert.description}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function SummaryRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3">
      <div className="text-sm text-muted">{label}</div>
      <div className="text-sm font-medium text-text">{value}</div>
    </div>
  );
}

function approvalTone(status: string) {
  if (status === "approved" || status === "implemented") return "success";
  if (status === "in_review") return "warning";
  if (status === "rejected" || status === "failed") return "danger";
  return "neutral";
}

function verificationTone(status: RequirementVerificationStatus) {
  if (status === "verified") return "success";
  if (status === "failed" || status === "not_covered") return "danger";
  if (status === "at_risk" || status === "partially_verified") return "warning";
  return "neutral";
}

function humanizeStatus(status: string) {
  return status.replaceAll("_", " ");
}

function humanizeDecisionSource(source: string) {
  if (!source) return "Not specified";
  return source.charAt(0).toUpperCase() + source.slice(1);
}

function labelForProfile(profile: ValidationProfile) {
  return PROFILES.find((item) => item.value === profile)?.label || profile;
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
