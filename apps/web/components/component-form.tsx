"use client";

import { useEffect, useMemo, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { getLabels, type DomainProfile } from "@/lib/labels";
import { useToast } from "@/lib/toast-context";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { Component } from "@/lib/types";

type ComponentTypeValue = "battery" | "motor" | "flight_controller" | "camera" | "sensor" | "frame" | "software_module" | "other";
type ComponentStatusValue = "draft" | "selected" | "validated" | "retired";

const COMPONENT_LABEL: Record<DomainProfile, string> = {
  engineering: "Component",
  manufacturing: "Component",
  personal: "Element",
  custom: "Component",
};

const STATUS_OPTIONS: Record<DomainProfile, { value: ComponentStatusValue; label: string }[]> = {
  engineering: [
    { value: "draft", label: "draft" },
    { value: "selected", label: "selected" },
    { value: "validated", label: "validated" },
    { value: "retired", label: "retired" },
  ],
  manufacturing: [
    { value: "draft", label: "draft" },
    { value: "selected", label: "selected" },
    { value: "validated", label: "released" },
    { value: "retired", label: "retired" },
  ],
  personal: [
    { value: "draft", label: "draft" },
    { value: "selected", label: "chosen" },
    { value: "validated", label: "ready" },
    { value: "retired", label: "archived" },
  ],
  custom: [
    { value: "draft", label: "draft" },
    { value: "selected", label: "selected" },
    { value: "validated", label: "validated" },
    { value: "retired", label: "retired" },
  ],
};

const TYPE_OPTIONS: { value: ComponentTypeValue; label: string }[] = [
  { value: "battery", label: "battery" },
  { value: "motor", label: "motor" },
  { value: "flight_controller", label: "flight controller" },
  { value: "camera", label: "camera" },
  { value: "sensor", label: "sensor" },
  { value: "frame", label: "frame" },
  { value: "software_module", label: "software module" },
  { value: "other", label: "other" },
];

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  name: z.string().min(1),
  description: z.string().optional().default(""),
  type: z.enum(["battery", "motor", "flight_controller", "camera", "sensor", "frame", "software_module", "other"]),
  part_number: z.string().optional().default(""),
  supplier: z.string().optional().default(""),
  status: z.enum(["draft", "selected", "validated", "retired"]),
  metadata_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

type ProjectOption = {
  id: string;
  code: string;
  name: string;
  domain_profile: DomainProfile;
  component_count: number;
};

function buildComponentKey(projectCode: string, count: number) {
  const normalized = (projectCode || "CMP").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").toUpperCase() || "CMP";
  return `${normalized}-CMP-${String(count + 1).padStart(3, "0")}`;
}

export function ComponentForm({
  projects,
  initialProjectId,
  initial,
}: {
  projects: ProjectOption[];
  initialProjectId?: string;
  initial?: Partial<Component>;
}) {
  const router = useRouter();
  const { showToast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || initialProjectId || projects[0]?.id || "",
      key: initial?.key || "",
      name: initial?.name || "",
      description: initial?.description || "",
      type: initial?.type || "other",
      part_number: initial?.part_number || "",
      supplier: initial?.supplier || "",
      status: initial?.status || "draft",
      metadata_json: JSON.stringify(initial?.metadata_json || {}, null, 2),
    },
  });

  const projectId = useWatch({ control: form.control, name: "project_id" });
  const currentProject = useMemo(() => projects.find((project) => project.id === projectId) || projects[0], [projectId, projects]);
  const labels = getLabels(currentProject?.domain_profile);
  const componentLabel = COMPONENT_LABEL[currentProject?.domain_profile ?? "engineering"];
  const statusOptions = STATUS_OPTIONS[currentProject?.domain_profile ?? "engineering"];

  useEffect(() => {
    if (!currentProject) return;
    if (initial?.id) return;
    form.setValue("key", buildComponentKey(currentProject.code, currentProject.component_count), { shouldDirty: false, shouldTouch: false });
  }, [currentProject, form, initial?.id]);

  useEffect(() => {
    if (!form.getValues("project_id") && currentProject?.id) {
      form.setValue("project_id", currentProject.id, { shouldDirty: false, shouldTouch: false });
    }
  }, [currentProject, form]);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const metadata_json = values.metadata_json?.trim() ? JSON.parse(values.metadata_json) : {};
      if (initial?.id) {
        await api.updateComponent(initial.id, { ...values, metadata_json });
        router.push(`/components/${initial.id}`);
      } else {
        const created = await api.createComponent({ ...values, metadata_json });
        showToast({
          message: `${componentLabel} created`,
          action: {
            label: `View ${labels.links.toLowerCase()}`,
            href: `/projects/${values.project_id}/traceability`,
          },
        });
        router.push(`/components/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Unable to save ${componentLabel.toLowerCase()}`);
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <Select {...form.register("project_id")}>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.code} - {project.name}
              </option>
            ))}
          </Select>
          <p className="text-xs text-muted">Select the project that owns this {componentLabel.toLowerCase()}.</p>
        </div>
        <Input placeholder={`${componentLabel} key`} readOnly {...form.register("key")} />
      </div>
      <Input placeholder={`${componentLabel} name`} {...form.register("name")} />
      <Textarea placeholder={`Describe this ${componentLabel.toLowerCase()}.`} rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("type")}>
          {TYPE_OPTIONS.map((option) => (
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
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Part number (optional)" {...form.register("part_number")} />
        <Input placeholder="Supplier (optional)" {...form.register("supplier")} />
      </div>
      <Textarea placeholder='Metadata JSON, for example {"repository": "git@example.com:repo.git"}' rows={6} {...form.register("metadata_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">{`Save ${componentLabel}`}</Button>
    </form>
  );
}
