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
import type { Block } from "@/lib/types";
import { FormFooter, InlineHelp } from "@/components/form-helpers";

type BlockKindValue = "system" | "subsystem" | "assembly" | "component" | "software" | "interface" | "other";
type BlockStatusValue = "draft" | "in_review" | "approved" | "rejected" | "obsolete";

type ProjectOption = {
  id: string;
  code: string;
  name: string;
  domain_profile: DomainProfile;
  block_count?: number;
};

export const BLOCK_KIND_OPTIONS: Record<DomainProfile, { value: BlockKindValue; label: string }[]> = {
  engineering: [
    { value: "system", label: "system" },
    { value: "subsystem", label: "subsystem" },
    { value: "assembly", label: "assembly" },
    { value: "component", label: "component" },
    { value: "software", label: "software" },
    { value: "interface", label: "interface" },
    { value: "other", label: "other" },
  ],
  manufacturing: [
    { value: "system", label: "production system" },
    { value: "subsystem", label: "subassembly" },
    { value: "assembly", label: "machine assembly" },
    { value: "component", label: "workstation component" },
    { value: "software", label: "automation software" },
    { value: "interface", label: "handoff interface" },
    { value: "other", label: "other" },
  ],
  personal: [
    { value: "system", label: "device" },
    { value: "subsystem", label: "service" },
    { value: "assembly", label: "network" },
    { value: "component", label: "configuration" },
    { value: "software", label: "app" },
    { value: "interface", label: "interface" },
    { value: "other", label: "other" },
  ],
  custom: [
    { value: "system", label: "system" },
    { value: "subsystem", label: "subsystem" },
    { value: "assembly", label: "assembly" },
    { value: "component", label: "component" },
    { value: "software", label: "software" },
    { value: "interface", label: "interface" },
    { value: "other", label: "other" },
  ],
};

const STATUS_OPTIONS: Record<DomainProfile, { value: BlockStatusValue; label: string }[]> = {
  engineering: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "obsolete", label: "obsolete" },
  ],
  manufacturing: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "review" },
    { value: "approved", label: "released" },
    { value: "rejected", label: "rework" },
    { value: "obsolete", label: "retired" },
  ],
  personal: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "under review" },
    { value: "approved", label: "ready" },
    { value: "rejected", label: "needs work" },
    { value: "obsolete", label: "archived" },
  ],
  custom: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "obsolete", label: "obsolete" },
  ],
};

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  name: z.string().min(1),
  description: z.string().optional().default(""),
  block_kind: z.enum(["system", "subsystem", "assembly", "component", "software", "interface", "other"]),
  abstraction_level: z.enum(["logical", "physical"]),
  status: z.enum(["draft", "in_review", "approved", "rejected", "obsolete"]),
  owner: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export function BlockForm({
  initial,
  labels: providedLabels,
  profile,
  projects = [],
  initialProjectId,
}: {
  initial?: Partial<Block>;
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
      name: initial?.name || "",
      description: initial?.description || "",
      block_kind: initial?.block_kind || "system",
      abstraction_level: initial?.abstraction_level || "logical",
      status: initial?.status || "draft",
      owner: initial?.owner || "",
    },
  });
  const selectedProjectId = useWatch({ control: form.control, name: "project_id" });
  const currentProject = projects.find((project) => project.id === selectedProjectId) || projects[0];
  const resolvedProfile = profile ?? currentProject?.domain_profile ?? "engineering";
  const blockKindOptions = BLOCK_KIND_OPTIONS[resolvedProfile];
  const statusOptions = STATUS_OPTIONS[resolvedProfile];

  useEffect(() => {
    if (initial?.id) return;
    if (!currentProject) return;
    if (form.getValues("key")) return;
    const count = currentProject.block_count ?? 0;
    const prefix = currentProject.code.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").toUpperCase() || "BLK";
    form.setValue("key", `${prefix}-BLK-${String(count + 1).padStart(3, "0")}`, { shouldDirty: false, shouldTouch: false });
  }, [currentProject, form, initial?.id]);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      if (initial?.id) {
        await api.updateBlock(initial.id, values);
        router.push(`/blocks/${initial.id}`);
      } else {
        const created = await api.createBlock(values);
        showToast({
          message: `${labels.blocks} created`,
          action: {
            label: `Add a ${labels.testCases}`,
            href: `/projects/${values.project_id}/tests`,
          },
        });
        router.push(`/blocks/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save block");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <Select {...form.register("project_id")} disabled={!projects.length}>
            {(projects.length ? projects : currentProject ? [currentProject] : []).map((project) => (
              <option key={project.id} value={project.id}>
                {project.code} - {project.name}
              </option>
            ))}
          </Select>
          <InlineHelp>Select the project that owns this {labels.block.toLowerCase()}.</InlineHelp>
        </div>
        <Input placeholder={`${labels.block} key`} readOnly {...form.register("key")} />
      </div>
      <Input placeholder={`${labels.block} name`} {...form.register("name")} />
      <Textarea placeholder={labels.block_description} rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("block_kind")}>
          {blockKindOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select {...form.register("abstraction_level")}>
          <option value="logical">logical</option>
          <option value="physical">physical</option>
        </Select>
        <Select {...form.register("status")}>
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Input placeholder="Owner" {...form.register("owner")} />
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <FormFooter submitLabel={`Save ${labels.block}`} onCancel={() => router.back()} />
    </form>
  );
}
