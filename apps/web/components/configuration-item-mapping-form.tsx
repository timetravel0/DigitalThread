"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type {
  ExternalArtifactVersion,
} from "@/lib/types";

type EditableInternalObjectType = "requirement" | "block" | "test_case";
type InternalConfigurationItemKind = "internal_requirement" | "internal_block" | "internal_test_case";

const internalSchema = z.object({
  item_kind: z.enum(["internal_requirement", "internal_block", "internal_test_case"]),
  internal_object_type: z.enum(["requirement", "block", "test_case"]),
  internal_object_id: z.string().min(1),
  internal_object_version: z.coerce.number().int().min(1),
  role_label: z.string().optional().default(""),
  notes: z.string().optional().default(""),
});

const externalSchema = z.object({
  item_kind: z.literal("external_artifact_version"),
  external_artifact_version_id: z.string().min(1),
  role_label: z.string().optional().default(""),
  notes: z.string().optional().default(""),
});

type InternalFormValues = z.infer<typeof internalSchema>;
type ExternalFormValues = z.infer<typeof externalSchema>;

const internalKindMap: Record<EditableInternalObjectType, InternalConfigurationItemKind> = {
  requirement: "internal_requirement",
  block: "internal_block",
  test_case: "internal_test_case",
};

export function InternalConfigurationItemMappingForm({
  contextId,
  internalOptions,
  disabled = false,
}: {
  contextId: string;
  internalOptions: { object_type: EditableInternalObjectType; object_id: string; label: string; version: number }[];
  disabled?: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const defaultOption = internalOptions[0];
  const form = useForm<InternalFormValues>({
    resolver: zodResolver(internalSchema),
    defaultValues: {
      item_kind: defaultOption ? internalKindMap[defaultOption.object_type] : "internal_requirement",
      internal_object_type: defaultOption?.object_type || "requirement",
      internal_object_id: defaultOption?.object_id || "",
      internal_object_version: defaultOption?.version || 1,
      role_label: "",
      notes: "",
    },
  });

  const selectedType = form.watch("internal_object_type") as EditableInternalObjectType;
  const availableOptions = useMemo(
    () => internalOptions.filter((option) => option.object_type === selectedType),
    [internalOptions, selectedType]
  );

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    if (disabled) {
      setError("This configuration context is frozen, released, or obsolete and cannot accept new mappings.");
      return;
    }
    try {
      await api.createConfigurationContextItem(contextId, {
        item_kind: values.item_kind,
        internal_object_type: values.internal_object_type,
        internal_object_id: values.internal_object_id,
        internal_object_version: values.internal_object_version,
        role_label: values.role_label || null,
        notes: values.notes || null,
      });
      router.refresh();
      form.reset({
        ...values,
        role_label: "",
        notes: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save configuration item");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      {internalOptions.length ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Select
              disabled={disabled}
              {...form.register("internal_object_type", {
                onChange: (event) => {
                  const nextType = event.target.value as EditableInternalObjectType;
                  const nextOption = internalOptions.find((option) => option.object_type === nextType) || internalOptions[0];
                  form.setValue("item_kind", internalKindMap[nextType] || "internal_requirement");
                  form.setValue("internal_object_id", nextOption?.object_id || "");
                  form.setValue("internal_object_version", nextOption?.version || 1);
                },
              })}
            >
              <option value="requirement">internal requirement</option>
              <option value="block">internal block</option>
              <option value="test_case">internal test case</option>
            </Select>
            <Select
              disabled={disabled}
              {...form.register("internal_object_id", {
                onChange: (event) => {
                  const nextOption = internalOptions.find((option) => option.object_id === event.target.value);
                  if (nextOption) form.setValue("internal_object_version", nextOption.version);
                },
              })}
            >
              {availableOptions.map((option) => (
                <option key={option.object_id} value={option.object_id}>
                  {option.label} v{option.version}
                </option>
              ))}
            </Select>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input type="number" min={1} step={1} placeholder="Internal object version" disabled={disabled} {...form.register("internal_object_version", { valueAsNumber: true })} />
            <Input placeholder="Role label" disabled={disabled} {...form.register("role_label")} />
          </div>
          <Textarea placeholder="Notes" rows={3} disabled={disabled} {...form.register("notes")} />
          {error ? <div className="text-sm text-danger">{error}</div> : null}
          <Button type="submit" disabled={disabled}>Add internal item</Button>
        </>
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No internal items available in this project yet.</div>
      )}
    </form>
  );
}

export function ExternalConfigurationItemMappingForm({
  contextId,
  artifactVersions,
  disabled = false,
}: {
  contextId: string;
  artifactVersions: ExternalArtifactVersion[];
  disabled?: boolean;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<ExternalFormValues>({
    resolver: zodResolver(externalSchema),
    defaultValues: {
      item_kind: "external_artifact_version",
      external_artifact_version_id: artifactVersions[0]?.id || "",
      role_label: "",
      notes: "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    if (disabled) {
      setError("This configuration context is frozen, released, or obsolete and cannot accept new mappings.");
      return;
    }
    try {
      await api.createConfigurationContextItem(contextId, {
        item_kind: values.item_kind,
        external_artifact_version_id: values.external_artifact_version_id,
        role_label: values.role_label || null,
        notes: values.notes || null,
      });
      router.refresh();
      form.reset({
        item_kind: "external_artifact_version",
        external_artifact_version_id: artifactVersions[0]?.id || "",
        role_label: "",
        notes: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save configuration item");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      {artifactVersions.length ? (
        <>
          <Select disabled={disabled} {...form.register("external_artifact_version_id")}>
            {artifactVersions.map((version) => (
              <option key={version.id} value={version.id}>
                {version.version_label}{version.revision_label ? ` / ${version.revision_label}` : ""}
              </option>
            ))}
          </Select>
          <div className="grid gap-4 md:grid-cols-2">
            <Input placeholder="Role label" disabled={disabled} {...form.register("role_label")} />
            <Input value="Authoritative external reference" readOnly disabled />
          </div>
          <Textarea placeholder="Notes" rows={3} disabled={disabled} {...form.register("notes")} />
          {error ? <div className="text-sm text-danger">{error}</div> : null}
          <Button type="submit" disabled={disabled}>Add external item</Button>
        </>
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No external artifact versions are available in this project yet.</div>
      )}
    </form>
  );
}
