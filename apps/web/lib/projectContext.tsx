"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { DomainProfile, LabelSet } from "./labels";
import { getLabels } from "./labels";
import { api } from "./api-client";
import type { ProjectTabStats } from "./types";

export interface ProjectContextValue {
  projectId: string;
  profile: DomainProfile;
  labels: LabelSet;
  advancedMode: boolean;
  tabStats: ProjectTabStats | null;
  setTabStats: (value: ProjectTabStats | null) => void;
  setAdvancedMode: (v: boolean) => void;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

export function ProjectProvider({
  children,
  projectId,
  profile,
}: {
  children: React.ReactNode;
  projectId: string;
  profile: DomainProfile | null | undefined;
}) {
  const resolvedProfile = profile ?? "engineering";
  const storageKey = `threadlite-project-${projectId}-advanced-mode`;
  const [advancedMode, setAdvancedModeState] = useState(false);
  const [tabStats, setTabStats] = useState<ProjectTabStats | null>(null);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(storageKey);
      setAdvancedModeState(stored === "1");
    } catch {
      setAdvancedModeState(false);
    }
  }, [storageKey]);

  useEffect(() => {
    let cancelled = false;
    setTabStats(null);
    api.projectTabStats(projectId)
      .then((stats) => {
        if (!cancelled) {
          setTabStats(stats);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTabStats(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const setAdvancedMode = (value: boolean) => {
    setAdvancedModeState(value);
    try {
      window.localStorage.setItem(storageKey, value ? "1" : "0");
    } catch {
      // ignore storage failures
    }
  };

  const labels = useMemo(() => getLabels(resolvedProfile), [resolvedProfile]);

  return (
    <ProjectContext.Provider value={{ projectId, profile: resolvedProfile, labels, advancedMode, tabStats, setTabStats, setAdvancedMode }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject(): ProjectContextValue {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("useProject must be used inside ProjectProvider");
  return ctx;
}
