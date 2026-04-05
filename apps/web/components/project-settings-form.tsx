"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api-client";
import type { Project, DomainProfile } from "@/lib/types";
import { Button } from "@/components/ui";
import { ProjectProfileSelector } from "@/components/project-profile-selector";

export function ProjectSettingsForm({ project }: { project: Project }) {
  const router = useRouter();
  const [profile, setProfile] = useState<DomainProfile>(project.domain_profile);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateProject(project.id, { domain_profile: profile });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save project settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
        Changing the domain profile updates labels only. No data is lost.
      </div>
      <ProjectProfileSelector value={profile} onChange={setProfile} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <div className="flex flex-wrap gap-2">
        <Button onClick={submit} disabled={saving}>
          {saving ? "Saving..." : "Save settings"}
        </Button>
      </div>
    </div>
  );
}
