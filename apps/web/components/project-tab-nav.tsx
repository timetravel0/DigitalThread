"use client";

import Link from "next/link";
import type { DomainProfile, LabelSet } from "@/lib/labels";
import { getTabGroups } from "@/lib/tabConfig";
import type { ProjectTabStats } from "@/lib/types";

const tabLabels: Record<string, (labels: LabelSet) => string> = {
  requirements: (labels) => labels.requirements,
  blocks: (labels) => labels.blocks,
  tests: (labels) => labels.testCases,
  traceability: () => "Traceability",
  matrix: () => "Matrix",
  baselines: (labels) => labels.baselines,
  "change-requests": (labels) => labels.changeRequests,
  "non-conformities": (labels) => labels.nonConformities,
  "review-queue": () => "Review Queue",
  validation: () => "Validation",
  import: () => "Import",
  "simulation-evidence": (labels) => labels.simulationEvidence,
  "operational-evidence": (labels) => labels.operationalEvidence,
  "operational-runs": (labels) => labels.operationalRun,
  sysml: () => "SysML",
  "step-ap242": () => "STEP AP242",
  fmi: () => "FMI",
  "authoritative-sources": () => "Authoritative Sources",
  software: () => "Software",
};

const STATS_TAB_MAP: Partial<Record<string, keyof ProjectTabStats>> = {
  requirements: "requirements",
  blocks: "blocks",
  tests: "tests",
  baselines: "baselines",
  "change-requests": "change_requests",
  "non-conformities": "non_conformities",
  "simulation-evidence": "simulation_evidence",
  "operational-evidence": "operational_evidence",
  "operational-runs": "operational_runs",
};

export function ProjectTabNav({
  projectId,
  profile,
  labels,
  section,
  advancedMode,
  tabStats,
  setAdvancedMode,
}: {
  projectId: string;
  profile: DomainProfile;
  labels: LabelSet;
  section: string;
  advancedMode: boolean;
  tabStats?: ProjectTabStats | null;
  setAdvancedMode: (value: boolean) => void;
}) {
  const { core, advanced, hasAdvanced } = getTabGroups(profile, advancedMode);

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <div className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted">Core</div>
        <div className="flex flex-wrap items-center gap-2">
          {core.map((tab) => (
            <TabChip key={tab} tab={tab} section={section} projectId={projectId} labels={labels} tabStats={tabStats} />
          ))}
        </div>
      </div>

      {hasAdvanced ? (
        <div className="rounded-2xl border border-dashed border-line/80 bg-panel/50 px-3 py-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted">More</div>
              <div className="text-xs text-muted">
                {advancedMode
                  ? "Advanced views are visible when you need them."
                  : "Advanced views are hidden to keep the workspace focused."}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setAdvancedMode(!advancedMode)}
              className="text-xs text-muted underline decoration-dashed underline-offset-4 hover:text-text"
            >
              {advancedMode ? "Hide advanced views" : "Show advanced views"}
            </button>
          </div>
          {advancedMode ? (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {advanced.map((tab) => (
                <TabChip key={tab} tab={tab} section={section} projectId={projectId} labels={labels} tabStats={tabStats} />
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function TabChip({
  tab,
  section,
  projectId,
  labels,
  tabStats,
}: {
  tab: string;
  section: string;
  projectId: string;
  labels: LabelSet;
  tabStats?: ProjectTabStats | null;
}) {
  const active = tab === (section || "");
  const href = tab ? `/projects/${projectId}/${tab}` : `/projects/${projectId}`;
  const label = tabLabels[tab] ? tabLabels[tab](labels) : tab;
  return (
    <Link
      href={href}
      className={`rounded-full border px-3 py-1.5 text-sm ${active ? "border-accent bg-accent/10 text-accent" : "border-line text-text hover:bg-white/5"}`}
    >
      {label}
      {tabStats && STATS_TAB_MAP[tab] !== undefined && (
        <span
          className={`ml-1.5 inline-block h-1.5 w-1.5 rounded-full ${(tabStats[STATS_TAB_MAP[tab]!] ?? 0) > 0 ? "bg-success" : "bg-danger/60"}`}
        />
      )}
    </Link>
  );
}
