"use client";

import { getLabels, type DomainProfile } from "@/lib/labels";

const PROFILES: { key: DomainProfile; icon: string; title: string; description: string }[] = [
  {
    key: "engineering",
    icon: "🚀",
    title: "Technical Engineering",
    description: "Requirements, blocks, test cases, SysML traceability. For engineering teams needing full Digital Thread coverage.",
  },
  {
    key: "manufacturing",
    icon: "🏭",
    title: "Manufacturing / SME",
    description: "Specifications, components, quality checks, and change orders for production or quality teams.",
  },
  {
    key: "personal",
    icon: "🏠",
    title: "Personal Project",
    description: "Goals, elements, checks, and snapshots for homelabs, DIY, or solo projects.",
  },
];

export function ProjectProfileSelector({
  value,
  onChange,
}: {
  value: DomainProfile;
  onChange: (profile: DomainProfile) => void;
}) {
  const labels = getLabels(value);
  return (
    <div className="space-y-3">
      <div className="text-sm font-medium text-text">Domain profile</div>
      <div className="grid gap-3 md:grid-cols-3">
        {PROFILES.map((profile) => {
          const active = profile.key === value;
          return (
            <button
              key={profile.key}
              type="button"
              onClick={() => onChange(profile.key)}
              className={`rounded-2xl border p-4 text-left transition ${active ? "border-accent bg-accent/10 ring-2 ring-accent/40" : "border-line bg-panel2 hover:border-accent/50"}`}
            >
              <div className="text-2xl">{profile.icon}</div>
              <div className="mt-3 font-semibold">{profile.title}</div>
              <div className="mt-1 text-sm text-muted">{profile.description}</div>
              <div className="mt-3 text-xs uppercase tracking-[0.2em] text-muted">
                {labels.requirement} / {labels.block} / {labels.testCase}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
