"use client";

import { useState } from "react";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui";

export function SeedButton() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="space-y-2">
      <Button
        onClick={async () => {
          setBusy(true);
          setError(null);
          try {
            await api.seedDemo();
            window.location.reload();
          } catch {
            setError("Seed failed. Check that the backend is running.");
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? "Seeding..." : "Seed demo"}
      </Button>
      {error ? <div className="text-xs text-danger">{error}</div> : null}
    </div>
  );
}
