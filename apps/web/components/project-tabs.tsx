"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useProject } from "@/lib/projectContext";
import { getTabGroups, getWorkflowStrip } from "@/lib/tabConfig";
import { ProjectTabNav } from "@/components/project-tab-nav";
import { Badge } from "@/components/ui";

export function ProjectTabs({ section }: { section: string }) {
  const { projectId, profile, labels, advancedMode, setAdvancedMode, tabStats, dashboard } = useProject();
  const { advancedAvailable } = getTabGroups(profile, true);
  const workflow = getWorkflowStrip({ projectId, labels, tabStats, dashboard });

  useEffect(() => {
    if (section && advancedAvailable.includes(section as any) && !advancedMode) {
      setAdvancedMode(true);
    }
  }, [advancedAvailable, advancedMode, section, setAdvancedMode]);

  return (
    <div className="space-y-4">
      <WorkflowStrip workflow={workflow} />
      <ProjectTabNav projectId={projectId} profile={profile} labels={labels} section={section} advancedMode={advancedMode} setAdvancedMode={setAdvancedMode} tabStats={tabStats} />
    </div>
  );
}

function WorkflowStrip({ workflow }: { workflow: ReturnType<typeof getWorkflowStrip> }) {
  return (
    <div className="rounded-2xl border border-line bg-panel2 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[0.65rem] font-semibold uppercase tracking-[0.24em] text-muted">Recommended workflow</div>
          <div className="mt-1 text-sm text-muted">
            Follow this path first. Advanced sections stay available, but the thread starts here.
          </div>
        </div>
        <div className="text-right text-xs text-muted">
          <div>{workflow.summary}</div>
          <div>{workflow.completedCount}/{workflow.totalCount} steps complete</div>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-5">
        {workflow.steps.map((step, index) => {
          const stateTone = step.state === "complete" ? "border-success/30 bg-success/5 text-success" : step.state === "next" ? "border-accent/40 bg-accent/10 text-accent" : "border-line bg-panel text-text";
          const countTone = step.state === "complete" ? "text-success" : step.state === "next" ? "text-accent" : "text-muted";
          return (
            <Link key={step.key} href={step.href} className={`rounded-2xl border p-4 transition-colors hover:border-accent/50 ${stateTone}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="text-xs uppercase tracking-[0.22em] text-muted">Step {index + 1}</div>
                <Badge tone={step.state === "complete" ? "success" : step.state === "next" ? "accent" : "neutral"}>
                  {step.state === "complete" ? "Done" : step.state === "next" ? "Next" : "Later"}
                </Badge>
              </div>
              <div className="mt-2 text-sm font-semibold">{step.label}</div>
              <div className="mt-1 text-sm text-muted">{step.description}</div>
              <div className={`mt-3 text-xs uppercase tracking-[0.2em] ${countTone}`}>{step.count > 0 ? `${step.count} item${step.count === 1 ? "" : "s"}` : "Empty"}</div>
            </Link>
          );
        })}
      </div>
      <div className="mt-4 rounded-xl border border-dashed border-line/80 bg-background/40 px-3 py-2 text-sm text-muted">
        First-time users should start at requirements, then add realization, then checks, then inspect traceability, then review evidence.
      </div>
    </div>
  );
}
