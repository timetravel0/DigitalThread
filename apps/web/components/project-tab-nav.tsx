"use client";

import Link from "next/link";
import type { DomainProfile, LabelSet } from "@/lib/labels";
import { getVisibleTabs } from "@/lib/tabConfig";

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

export function ProjectTabNav({
  projectId,
  profile,
  labels,
  section,
  advancedMode,
  setAdvancedMode,
}: {
  projectId: string;
  profile: DomainProfile;
  labels: LabelSet;
  section: string;
  advancedMode: boolean;
  setAdvancedMode: (value: boolean) => void;
}) {
  const tabs = getVisibleTabs(profile, advancedMode);

  return (
    <div className="flex flex-wrap items-center gap-2">
      {tabs.map((tab) => {
        const active = tab === (section || "");
        const href = tab ? `/projects/${projectId}/${tab}` : `/projects/${projectId}`;
        const label = tabLabels[tab] ? tabLabels[tab](labels) : tab;
        return (
          <Link
            key={tab}
            href={href}
            className={`rounded-full border px-3 py-1.5 text-sm ${active ? "border-accent bg-accent/10 text-accent" : "border-line text-text hover:bg-white/5"}`}
          >
            {label}
          </Link>
        );
      })}
      {profile === "engineering" ? null : (
        <button
          type="button"
          onClick={() => setAdvancedMode(!advancedMode)}
          className="ml-auto text-xs text-muted underline decoration-dashed underline-offset-4 hover:text-text"
        >
          {advancedMode ? "Hide advanced tabs" : "Show advanced tabs"}
        </button>
      )}
    </div>
  );
}
