import type { DomainProfile } from "./labels";

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

const DEFAULT_TABS: Record<DomainProfile, ProjectTab[]> = {
  engineering: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "matrix",
    "baselines",
    "change-requests",
    "review-queue",
    "validation",
    "non-conformities",
    "import",
    "simulation-evidence",
    "operational-evidence",
    "operational-runs",
    "sysml",
    "step-ap242",
    "fmi",
    "authoritative-sources",
    "software",
  ],
  manufacturing: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "matrix",
    "baselines",
    "change-requests",
    "non-conformities",
    "review-queue",
    "validation",
    "import",
  ],
  personal: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "baselines",
    "change-requests",
    "import",
  ],
  custom: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "matrix",
    "baselines",
    "change-requests",
    "review-queue",
    "validation",
    "non-conformities",
    "import",
    "simulation-evidence",
    "operational-evidence",
    "operational-runs",
    "sysml",
    "step-ap242",
    "fmi",
    "authoritative-sources",
    "software",
  ],
};

const ADVANCED_TABS: Record<DomainProfile, ProjectTab[]> = {
  engineering: [],
  manufacturing: ["simulation-evidence", "operational-evidence", "operational-runs", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
  personal: ["simulation-evidence", "operational-evidence", "operational-runs", "matrix", "non-conformities", "review-queue", "validation", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
  custom: ["simulation-evidence", "operational-evidence", "operational-runs", "matrix", "non-conformities", "review-queue", "validation", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
};

export function getVisibleTabs(profile: DomainProfile | null | undefined, advancedMode: boolean): ProjectTab[] {
  const resolved = profile ?? "engineering";
  const base = DEFAULT_TABS[resolved] ?? DEFAULT_TABS.engineering;
  if (!advancedMode) return base;
  const advanced = ADVANCED_TABS[resolved] ?? [];
  return [...base, ...advanced];
}
