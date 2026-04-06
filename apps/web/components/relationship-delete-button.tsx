"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui";

export function RelationshipDeleteButton({ kind, id, label }: { kind: "link" | "sysml"; id: string; label: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Delete ${label}?`)) return;
    setBusy(true);
    try {
      if (kind === "link") {
        await api.deleteLink(id);
      } else {
        await api.deleteSysMLRelation(id);
      }
      router.refresh();
    } finally {
      setBusy(false);
    }
  };

  return (
    <Button type="button" variant="ghost" onClick={handleDelete} disabled={busy}>
      {busy ? "Deleting..." : "Delete"}
    </Button>
  );
}
