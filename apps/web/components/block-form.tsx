"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import { getLabels, type DomainProfile, type LabelSet } from "@/lib/labels";
import { useToast } from "@/lib/toast-context";
import type { Block } from "@/lib/types";

type BlockKindValue = "system" | "subsystem" | "assembly" | "component" | "software" | "interface" | "other";
type BlockStatusValue = "draft" | "in_review" | "approved" | "rejected" | "obsolete";

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
}: {
  initial?: Partial<Block>;
  labels?: LabelSet;
  profile?: DomainProfile;
}) {
  const router = useRouter();
  const { showToast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const labels = providedLabels || getLabels("engineering");
  const profileKey = profile ?? "engineering";
  const blockKindOptions = BLOCK_KIND_OPTIONS[profileKey];
  const statusOptions = STATUS_OPTIONS[profileKey];
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      name: initial?.name || "",
      description: initial?.description || "",
      block_kind: initial?.block_kind || "system",
      abstraction_level: initial?.abstraction_level || "logical",
      status: initial?.status || "draft",
      owner: initial?.owner || "",
    },
  });

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
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder={`${labels.block} key`} {...form.register("key")} />
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
      <Button type="submit">{`Save ${labels.block}`}</Button>
    </form>
  );
}
