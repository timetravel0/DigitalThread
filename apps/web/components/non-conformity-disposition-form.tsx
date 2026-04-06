"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import type { NonConformity, NonConformityDisposition } from "@/lib/types";
import { Button, Select, Textarea } from "@/components/ui";

const OPTIONS: { value: NonConformityDisposition; label: string; tone: "success" | "warning" | "danger" }[] = [
  { value: "accept", label: "Accept", tone: "success" },
  { value: "rework", label: "Rework", tone: "warning" },
  { value: "reject", label: "Reject", tone: "danger" },
];

export function NonConformityDispositionForm({
  nonConformityId,
  currentDisposition,
  currentStatus,
}: {
  nonConformityId: string;
  currentDisposition?: NonConformityDisposition | null;
  currentStatus: NonConformity["status"];
}) {
  const router = useRouter();
  const [disposition, setDisposition] = useState<NonConformityDisposition | "">(currentDisposition ?? "");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.updateNonConformity(nonConformityId, {
        disposition: disposition || null,
        status: currentStatus,
        review_comment: comment || null,
      });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save disposition");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        {OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setDisposition(option.value)}
            className={`rounded-xl border px-4 py-3 text-left text-sm font-medium transition ${
              disposition === option.value ? "border-accent bg-accent/15 text-accent" : "border-line bg-panel2 text-muted hover:border-accent/60"
            }`}
          >
            <div className="font-semibold">{option.label}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.2em]">{option.value}</div>
          </button>
        ))}
      </div>
      <Select value={disposition} onChange={(event) => setDisposition(event.target.value as NonConformityDisposition)}>
        <option value="">Select a disposition</option>
        {OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
      <Textarea
        value={comment}
        onChange={(event) => setComment(event.target.value)}
        placeholder="Add a short review comment or rationale for the deviation decision."
        rows={4}
      />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={busy || !disposition}>
          {busy ? "Saving..." : "Save disposition"}
        </Button>
        <div className="text-xs text-muted">The disposition stays separate from the NCR status and can be updated later.</div>
      </div>
    </div>
  );
}
