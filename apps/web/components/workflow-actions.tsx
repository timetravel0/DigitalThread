"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Button } from "@/components/ui";
import type { BlockStatus, RequirementStatus, TestCaseStatus, WorkflowActionPayload } from "@/lib/types";

type Status = RequirementStatus | BlockStatus | TestCaseStatus;

export function WorkflowActions({
  kind,
  id,
  status,
}: {
  kind: "requirement" | "block" | "test_case";
  id: string;
  status: Status;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);

  const run = async (action: string, fn: () => Promise<unknown>, refresh = true) => {
    setBusy(action);
    try {
      await fn();
      if (refresh) {
        router.refresh();
      }
    } finally {
      setBusy(null);
    }
  };

  const payload: WorkflowActionPayload = { actor: "local-user" };

  if (status === "approved") {
    return (
      <Button onClick={() => run("draft", async () => {
        const created =
          kind === "requirement"
            ? await api.createRequirementDraftVersion(id, payload)
            : kind === "block"
              ? await api.createBlockDraftVersion(id, payload)
              : await api.createTestCaseDraftVersion(id, payload);
        router.push(`/${kind === "test_case" ? "test-cases" : kind === "block" ? "blocks" : "requirements"}/${created.id}/edit`);
      }, false)}>
        {busy === "draft" ? "Working..." : "Create draft version and edit"}
      </Button>
    );
  }

  if (status === "draft" || status === "rejected") {
    return (
      <Button onClick={() => run("submit", async () => {
        if (kind === "requirement") await api.submitRequirement(id, payload);
        if (kind === "block") await api.submitBlock(id, payload);
        if (kind === "test_case") await api.submitTestCase(id, payload);
      })}>
        {busy === "submit" ? "Submitting..." : "Submit for review"}
      </Button>
    );
  }

  if (status === "in_review") {
    return (
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => run("approve", async () => {
          if (kind === "requirement") await api.approveRequirement(id, payload);
          if (kind === "block") await api.approveBlock(id, payload);
          if (kind === "test_case") await api.approveTestCase(id, payload);
        })}>
          {busy === "approve" ? "Approving..." : "Approve"}
        </Button>
        <Button variant="secondary" onClick={() => run("reject", async () => {
          if (kind === "requirement") await api.rejectRequirement(id, { ...payload, reason: "Needs revision" });
          if (kind === "block") await api.rejectBlock(id, { ...payload, reason: "Needs revision" });
          if (kind === "test_case") await api.rejectTestCase(id, { ...payload, reason: "Needs revision" });
        })}>
          {busy === "reject" ? "Rejecting..." : "Reject"}
        </Button>
        <Button variant="ghost" onClick={() => run("draft", async () => {
          if (kind === "requirement") await api.sendRequirementToDraft(id, { actor: "local-user", comment: "Back to draft" });
          if (kind === "block") await api.sendBlockToDraft(id, { actor: "local-user", comment: "Back to draft" });
          if (kind === "test_case") await api.sendTestCaseToDraft(id, { actor: "local-user", comment: "Back to draft" });
        })}>
          {busy === "draft" ? "Working..." : "Send back to draft"}
        </Button>
      </div>
    );
  }

  return null;
}
