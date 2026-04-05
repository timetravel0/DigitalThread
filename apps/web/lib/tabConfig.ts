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

export const TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
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

export const ADVANCED_TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
  engineering: [],
  manufacturing: ["simulation-evidence", "operational-evidence", "operational-runs", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
  personal: ["simulation-evidence", "operational-evidence", "operational-runs", "matrix", "non-conformities", "review-queue", "validation", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
  custom: ["simulation-evidence", "operational-evidence", "operational-runs", "matrix", "non-conformities", "review-queue", "validation", "sysml", "step-ap242", "fmi", "authoritative-sources", "software"],
};

export function getVisibleTabs(profile: DomainProfile | null | undefined, advancedMode: boolean): ProjectTab[] {
  const resolved = profile ?? "engineering";
  const base = TAB_VISIBILITY[resolved] ?? TAB_VISIBILITY.engineering;
  if (!advancedMode) return base;
  const advanced = ADVANCED_TAB_VISIBILITY[resolved] ?? [];
  return [...base, ...advanced];
}
