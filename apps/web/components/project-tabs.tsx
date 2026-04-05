"use client";

import { useProject } from "@/lib/projectContext";
import { ProjectTabNav } from "@/components/project-tab-nav";

export function ProjectTabs({ section }: { section: string }) {
  const { projectId, profile, labels, advancedMode, setAdvancedMode } = useProject();
  return <ProjectTabNav projectId={projectId} profile={profile} labels={labels} section={section} advancedMode={advancedMode} setAdvancedMode={setAdvancedMode} />;
}
