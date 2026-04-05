"use client";

import { useEffect } from "react";
import { useProject } from "@/lib/projectContext";
import { getTabGroups } from "@/lib/tabConfig";
import { ProjectTabNav } from "@/components/project-tab-nav";

export function ProjectTabs({ section }: { section: string }) {
  const { projectId, profile, labels, advancedMode, setAdvancedMode, tabStats } = useProject();
  const { advancedAvailable } = getTabGroups(profile, true);

  useEffect(() => {
    if (section && advancedAvailable.includes(section as any) && !advancedMode) {
      setAdvancedMode(true);
    }
  }, [advancedAvailable, advancedMode, section, setAdvancedMode]);

  return <ProjectTabNav projectId={projectId} profile={profile} labels={labels} section={section} advancedMode={advancedMode} setAdvancedMode={setAdvancedMode} tabStats={tabStats} />;
}
