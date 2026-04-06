"use client";

import type { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { useToast } from "@/lib/toast-context";
import type {
  LinkCreatePayload,
  LinkObjectType,
  RelationType,
  SysMLObjectType,
  SysMLRelationCreatePayload,
  SysMLRelationType,
} from "@/lib/types";
import { Badge, Button, EmptyState, Select, Textarea } from "@/components/ui";

const schema = z.object({
  target_id: z.string().min(1, "Choose a target object"),
  rationale: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export type RelationshipTarget = {
  id: string;
  label: string;
};

type RelationshipKind = "link" | "sysml";

type RelationshipLinkFormProps = {
  projectId: string;
  kind: RelationshipKind;
  sourceType: LinkObjectType | SysMLObjectType;
  sourceId: string;
  sourceLabel: string;
  relationType: RelationType | SysMLRelationType;
  relationLabel: string;
  targetType: LinkObjectType | SysMLObjectType;
  targetLabel: string;
  targets: RelationshipTarget[];
  title: string;
  description: string;
  emptyDescription: string;
  submitLabel: string;
  emptyAction?: ReactNode;
};

export function RelationshipLinkForm({
  projectId,
  kind,
  sourceType,
  sourceId,
  sourceLabel,
  relationType,
  relationLabel,
  targetType,
  targetLabel,
  targets,
  title,
  description,
  emptyDescription,
  submitLabel,
  emptyAction,
}: RelationshipLinkFormProps) {
  const router = useRouter();
  const { showToast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { target_id: "", rationale: "" },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      if (kind === "link") {
        const payload: LinkCreatePayload = {
          project_id: projectId,
          source_type: sourceType as LinkObjectType,
          source_id: sourceId,
          target_type: targetType as LinkObjectType,
          target_id: values.target_id,
          relation_type: relationType as RelationType,
          rationale: values.rationale || null,
        };
        await api.createLink(payload);
      } else {
        const payload: SysMLRelationCreatePayload = {
          project_id: projectId,
          source_type: sourceType as SysMLObjectType,
          source_id: sourceId,
          target_type: targetType as SysMLObjectType,
          target_id: values.target_id,
          relation_type: relationType as SysMLRelationType,
          rationale: values.rationale || null,
        };
        await api.createSysMLRelation(payload);
      }
      showToast({
        message: `${relationLabel} added`,
        action: {
          label: "Open traceability",
          href: `/projects/${projectId}/traceability`,
        },
      });
      router.refresh();
      form.reset({ target_id: "", rationale: "" });
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to save ${relationLabel.toLowerCase()}`);
    }
  });

  if (!targets.length) {
    return (
      <EmptyState
        title={`No ${targetLabel.toLowerCase()} available`}
        description={emptyDescription}
        action={emptyAction}
      />
    );
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="rounded-xl border border-line bg-panel2 p-3 text-sm">
        <div className="text-xs uppercase tracking-[0.2em] text-muted">Source</div>
        <div className="mt-1 font-medium">{sourceLabel}</div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Badge tone="neutral">{kind}</Badge>
          <Badge tone="accent">{relationLabel}</Badge>
        </div>
      </div>
      <div className="space-y-1">
        <div className="text-xs uppercase tracking-[0.2em] text-muted">Connect to {targetLabel.toLowerCase()}</div>
        <Select {...form.register("target_id")}>
          <option value="">Select {targetLabel.toLowerCase()}</option>
          {targets.map((target) => (
            <option key={target.id} value={target.id}>
              {target.label}
            </option>
          ))}
        </Select>
      </div>
      <Textarea placeholder="Why does this relation exist?" rows={3} {...form.register("rationale")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">{submitLabel}</Button>
      <div className="text-xs text-muted">{description}</div>
    </form>
  );
}
