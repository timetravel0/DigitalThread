"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui";
import type { WorkflowActionPayload } from "@/lib/types";

export function BaselineActions({ id, status }: { id: string; status: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const payload: WorkflowActionPayload = { actor: "local-user" };

  const run = async (action: string, fn: () => Promise<unknown>) => {
    setBusy(action);
    try {
      await fn();
      router.refresh();
    } finally {
      setBusy(null);
    }
  };

  if (status === "obsolete") {
    return <div className="text-sm text-muted">This baseline is obsolete.</div>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {status !== "released" ? (
        <Button onClick={() => run("release", async () => api.releaseBaseline(id, { ...payload, comment: "Release baseline" }))}>
          {busy === "release" ? "Releasing..." : "Release baseline"}
        </Button>
      ) : null}
      <Button variant="secondary" onClick={() => run("obsolete", async () => api.obsoleteBaseline(id, { ...payload, comment: "Mark obsolete" }))}>
        {busy === "obsolete" ? "Marking obsolete..." : "Mark obsolete"}
      </Button>
    </div>
  );
}
