"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import type { DomainProfile } from "@/lib/labels";
import { Button } from "@/components/ui";

const seedMeta: Record<DomainProfile, { action: () => Promise<{ project_id: string; seeded: boolean }>; label: string }> = {
  engineering: { action: () => api.seedDemo(), label: "Seed engineering demo" },
  manufacturing: { action: () => api.seedManufacturing(), label: "Seed manufacturing demo" },
  personal: { action: () => api.seedPersonal(), label: "Seed personal demo" },
  custom: { action: () => api.seedDemo(), label: "Seed demo" },
};

export function SeedButton({ profile }: { profile: DomainProfile }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const meta = seedMeta[profile] ?? seedMeta.engineering;
  return (
    <div className="space-y-2">
      <Button
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            await meta.action();
            window.location.reload();
          } catch {
            setError("Seed failed. Check that the backend is running.");
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Seeding..." : meta.label}
      </Button>
      {error ? <div className="text-xs text-danger">{error}</div> : null}
    </div>
  );
}
