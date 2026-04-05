"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import { getLabels, type DomainProfile, type LabelSet } from "@/lib/labels";
import { useToast } from "@/lib/toast-context";
import type { Requirement } from "@/lib/types";

type RequirementCategoryValue = "performance" | "safety" | "environment" | "operations" | "compliance";
type VerificationMethodValue = "analysis" | "inspection" | "test" | "demonstration";
type RequirementStatusValue = "draft" | "in_review" | "approved" | "rejected" | "implemented" | "verified" | "failed" | "obsolete" | "retired";

type ProjectOption = {
  id: string;
  code: string;
  name: string;
  domain_profile: DomainProfile;
  requirement_count?: number;
};

export const CATEGORY_OPTIONS: Record<DomainProfile, { value: RequirementCategoryValue; label: string }[]> = {
  engineering: [
    { value: "performance", label: "performance" },
    { value: "safety", label: "safety" },
    { value: "environment", label: "environment" },
    { value: "operations", label: "operations" },
    { value: "compliance", label: "compliance" },
  ],
  manufacturing: [
    { value: "performance", label: "quality" },
    { value: "operations", label: "production" },
    { value: "safety", label: "safety" },
    { value: "compliance", label: "compliance" },
    { value: "environment", label: "environment" },
  ],
  personal: [
    { value: "performance", label: "goal" },
    { value: "safety", label: "constraint" },
    { value: "operations", label: "infrastructure" },
    { value: "compliance", label: "maintenance" },
    { value: "environment", label: "other" },
  ],
  custom: [
    { value: "performance", label: "performance" },
    { value: "safety", label: "safety" },
    { value: "environment", label: "environment" },
    { value: "operations", label: "operations" },
    { value: "compliance", label: "compliance" },
  ],
};

export const VERIFICATION_METHOD_OPTIONS: Record<DomainProfile, { value: VerificationMethodValue; label: string }[]> = {
  engineering: [
    { value: "analysis", label: "analysis" },
    { value: "inspection", label: "inspection" },
    { value: "test", label: "test" },
    { value: "demonstration", label: "demonstration" },
  ],
  manufacturing: [
    { value: "analysis", label: "measurement analysis" },
    { value: "inspection", label: "inspection" },
    { value: "test", label: "production test" },
    { value: "demonstration", label: "process validation" },
  ],
  personal: [
    { value: "analysis", label: "estimate" },
    { value: "inspection", label: "check" },
    { value: "test", label: "try" },
    { value: "demonstration", label: "demo" },
  ],
  custom: [
    { value: "analysis", label: "analysis" },
    { value: "inspection", label: "inspection" },
    { value: "test", label: "test" },
    { value: "demonstration", label: "demonstration" },
  ],
};

const STATUS_OPTIONS: Record<DomainProfile, { value: RequirementStatusValue; label: string }[]> = {
  engineering: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "implemented", label: "implemented" },
    { value: "verified", label: "verified" },
    { value: "failed", label: "failed" },
    { value: "obsolete", label: "obsolete" },
    { value: "retired", label: "retired" },
  ],
  manufacturing: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "review" },
    { value: "approved", label: "released" },
    { value: "rejected", label: "rework" },
    { value: "implemented", label: "implemented" },
    { value: "verified", label: "verified" },
    { value: "failed", label: "failed" },
    { value: "obsolete", label: "obsolete" },
    { value: "retired", label: "retired" },
  ],
  personal: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "under review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "needs work" },
    { value: "implemented", label: "done" },
    { value: "verified", label: "verified" },
    { value: "failed", label: "failed" },
    { value: "obsolete", label: "archived" },
    { value: "retired", label: "retired" },
  ],
  custom: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "implemented", label: "implemented" },
    { value: "verified", label: "verified" },
    { value: "failed", label: "failed" },
    { value: "obsolete", label: "obsolete" },
    { value: "retired", label: "retired" },
  ],
};

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  title: z.string().min(1),
  description: z.string().optional().default(""),
  category: z.enum(["performance", "safety", "environment", "operations", "compliance"]),
  priority: z.enum(["low", "medium", "high", "critical"]),
  verification_method: z.enum(["analysis", "inspection", "test", "demonstration"]),
  status: z.enum(["draft", "in_review", "approved", "rejected", "implemented", "verified", "failed", "obsolete", "retired"]),
  parent_requirement_id: z.string().optional().or(z.literal("")),
  verification_criteria_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

export function RequirementForm({
  initial,
  onSaved,
  labels: providedLabels,
  profile,
  projects = [],
  initialProjectId,
}: {
  initial?: Partial<Requirement>;
  onSaved?: () => void;
  labels?: LabelSet;
  profile?: DomainProfile;
  projects?: ProjectOption[];
  initialProjectId?: string;
}) {
  const router = useRouter();
  const { showToast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const labels = providedLabels || getLabels("engineering");
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || initialProjectId || projects[0]?.id || "",
      key: initial?.key || "",
      title: initial?.title || "",
      description: initial?.description || "",
      category: initial?.category || "performance",
      priority: initial?.priority || "medium",
      verification_method: initial?.verification_method || "test",
      status: initial?.status || "draft",
      parent_requirement_id: initial?.parent_requirement_id || "",
      verification_criteria_json: JSON.stringify(initial?.verification_criteria_json || {}, null, 2),
    },
  });
  const selectedProjectId = useWatch({ control: form.control, name: "project_id" });
  const currentProject = projects.find((project) => project.id === selectedProjectId) || projects[0];
  const resolvedProfile = profile ?? currentProject?.domain_profile ?? "engineering";
  const categoryOptions = CATEGORY_OPTIONS[resolvedProfile];
  const verificationMethodOptions = VERIFICATION_METHOD_OPTIONS[resolvedProfile];
  const statusOptions = STATUS_OPTIONS[resolvedProfile];

  useEffect(() => {
    if (initial?.id) return;
    if (!currentProject) return;
    if (form.getValues("key")) return;
    const count = currentProject.requirement_count ?? 0;
    const prefix = currentProject.code.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").toUpperCase() || "REQ";
    form.setValue("key", `${prefix}-REQ-${String(count + 1).padStart(3, "0")}`, { shouldDirty: false, shouldTouch: false });
  }, [currentProject, form, initial?.id]);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const verification_criteria_json = values.verification_criteria_json?.trim()
        ? JSON.parse(values.verification_criteria_json)
        : {};
      if (initial?.id) {
        await api.updateRequirement(initial.id, { ...values, verification_criteria_json });
        onSaved?.();
        router.refresh();
        router.push(`/requirements/${initial.id}`);
      } else {
        const created = await api.createRequirement({ ...values, verification_criteria_json });
        showToast({
          message: `${labels.requirements} created`,
          action: {
            label: `Link to a ${labels.blocks}`,
            href: `/projects/${values.project_id}/traceability`,
          },
        });
        onSaved?.();
        router.push(`/requirements/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save requirement");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("project_id")} disabled={!projects.length}>
          {(projects.length ? projects : currentProject ? [currentProject] : []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.code} - {project.name}
            </option>
          ))}
        </Select>
        <Input placeholder={`${labels.requirement} key`} {...form.register("key")} />
      </div>
      <Input placeholder={`${labels.requirement} title`} {...form.register("title")} />
      <Textarea placeholder={labels.requirement_description} rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("category")}>
          {categoryOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select {...form.register("priority")}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="critical">critical</option>
        </Select>
        <Select {...form.register("verification_method")}>
          {verificationMethodOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select {...form.register("status")}>
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>
      <div className="space-y-1">
        <Input placeholder={`Parent ${labels.requirement} ID (optional)`} {...form.register("parent_requirement_id")} />
        <p className="text-xs text-muted">Related {labels.block} traceability is shown from the requirement detail page.</p>
      </div>
      <Textarea placeholder='Verification criteria JSON, for example {"telemetry_thresholds": {"battery_consumption_pct": {"max": 85}}}' rows={6} {...form.register("verification_criteria_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">{`Save ${labels.requirement}`}</Button>
    </form>
  );
}
