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

export const CORE_TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
  engineering: [
    "requirements",
    "blocks",
    "tests",
    "traceability",
    "matrix",
    "baselines",
    "change-requests",
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
    "matrix",
    "baselines",
    "change-requests",
  ],
};

export const ADVANCED_TAB_VISIBILITY: Record<DomainProfile, ProjectTab[]> = {
  engineering: ["review-queue", "validation", "non-conformities", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
  manufacturing: ["review-queue", "validation", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
  personal: ["matrix", "review-queue", "validation", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
  custom: ["review-queue", "validation", "non-conformities", "import", "simulation-evidence", "operational-evidence", "operational-runs", "sysml", "authoritative-sources", "software"],
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
