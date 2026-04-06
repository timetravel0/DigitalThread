import type { DomainProfile, LabelSet } from "./labels";
import type { Dashboard, ProjectTabStats } from "./types";

export type ProjectTab =
  | "requirements"
  | "blocks"
  | "tests"
  | "traceability"
  | "matrix"
  | "baselines"
  | "change-requests"
  | "non-conformities"
  | "review-queue"
  | "validation"
  | "import"
  | "simulation-evidence"
  | "operational-evidence"
  | "operational-runs"
  | "sysml"
  | "step-ap242"
  | "fmi"
  | "authoritative-sources"
  | "software";

export const CORE_TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
  engineering: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "baselines",
    "change-requests",
  ],
  manufacturing: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "baselines",
    "change-requests",
  ],
  personal: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "baselines",
    "change-requests",
  ],
  custom: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "baselines",
    "change-requests",
  ],
};

export const ADVANCED_TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
  engineering: ["matrix", "review-queue", "validation", "non-conformities", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
  manufacturing: ["matrix", "review-queue", "validation", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
  personal: ["matrix", "review-queue", "validation", "import"],
  custom: ["matrix", "review-queue", "validation", "non-conformities", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
};

export function getVisibleTabs(profile: DomainProfile | null | undefined, advancedMode: boolean): ProjectTab[] {
  const resolved = profile ?? "engineering";
  const base = CORE_TAB_VISIBILITY[resolved] ?? CORE_TAB_VISIBILITY.engineering;
  if (!advancedMode) return base;
  const advanced = ADVANCED_TAB_VISIBILITY[resolved] ?? [];
  return [...base, ...advanced];
}

export function getTabGroups(profile: DomainProfile | null | undefined, advancedMode: boolean) {
  const resolved = profile ?? "engineering";
  const core = CORE_TAB_VISIBILITY[resolved] ?? CORE_TAB_VISIBILITY.engineering;
  const advanced = ADVANCED_TAB_VISIBILITY[resolved] ?? [];
  return {
    core,
    advanced: advancedMode ? advanced : [],
    hasAdvanced: advanced.length > 0,
    advancedAvailable: advanced,
  };
}

export type WorkflowStepState = "complete" | "next" | "pending";

export interface WorkflowStep {
  key: "requirements" | "blocks" | "tests" | "traceability" | "evidence";
  label: string;
  href: string;
  description: string;
  state: WorkflowStepState;
  count: number;
}

export interface WorkflowStrip {
  steps: WorkflowStep[];
  nextStep: WorkflowStep;
  completedCount: number;
  totalCount: number;
  summary: string;
}

export function getWorkflowStrip({
  projectId,
  labels,
  tabStats,
  dashboard,
}: {
  projectId: string;
  labels: Pick<LabelSet, "requirements" | "blocks" | "testCases">;
  tabStats: ProjectTabStats | null;
  dashboard: Dashboard | null;
}): WorkflowStrip {
  const requirementsCount = tabStats?.requirements ?? dashboard?.kpis.total_requirements ?? 0;
  const blocksCount = tabStats?.blocks ?? 0;
  const testsCount = tabStats?.tests ?? 0;
  const traceabilityCount =
    (dashboard?.kpis.requirements_with_allocated_components ?? 0) +
    (dashboard?.kpis.requirements_with_verifying_tests ?? 0) +
    (dashboard?.recent_links?.length ?? 0);
  const evidenceCount = (tabStats?.simulation_evidence ?? 0) + (tabStats?.operational_evidence ?? 0) + (tabStats?.operational_runs ?? 0) + (tabStats?.baselines ?? 0) + (tabStats?.change_requests ?? 0) + (tabStats?.non_conformities ?? 0) + (dashboard?.kpis.open_change_requests ?? 0);

  const steps: Omit<WorkflowStep, "state">[] = [
    {
      key: "requirements",
      label: labels.requirements,
      href: `/projects/${projectId}/requirements`,
      description: "Capture the need, goal, or specification that anchors the project.",
      count: requirementsCount,
    },
    {
      key: "blocks",
      label: labels.blocks,
      href: `/projects/${projectId}/blocks`,
      description: "Add the parts or elements that realize each requirement.",
      count: blocksCount,
    },
    {
      key: "tests",
      label: labels.testCases,
      href: `/projects/${projectId}/tests`,
      description: "Create checks that prove the requirement is met.",
      count: testsCount,
    },
    {
      key: "traceability",
      label: "Traceability",
      href: `/projects/${projectId}/graph`,
      description: "Walk the links that connect needs, realization, and verification.",
      count: traceabilityCount,
    },
    {
      key: "evidence",
      label: "Evidence / Review",
      href: `/projects/${projectId}/baselines`,
      description: "Capture evidence and review snapshots that support decisions.",
      count: evidenceCount,
    },
  ];

  const nextIndex = steps.findIndex((step) => {
    if (step.key === "traceability") {
      return traceabilityCount === 0;
    }
    if (step.key === "evidence") {
      return evidenceCount === 0;
    }
    return step.count === 0;
  });

  const allComplete = nextIndex === -1;
  const resolvedSteps: WorkflowStep[] = steps.map((step, index) => ({
    ...step,
    state: allComplete ? "complete" : index < nextIndex ? "complete" : index === nextIndex ? "next" : "pending",
  }));
  const nextStep = allComplete ? resolvedSteps[resolvedSteps.length - 1] : resolvedSteps[nextIndex];
  const completedCount = resolvedSteps.filter((step) => step.state === "complete").length;
  const summary = allComplete ? "Primary workflow complete. Use advanced views when needed." : `Next: ${nextStep.label}.`;

  return {
    steps: resolvedSteps,
    nextStep,
    completedCount,
    totalCount: resolvedSteps.length,
    summary,
  };
}
