"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { ConfigurationItemKind, FederatedInternalObjectType } from "@/lib/types";

type InternalOption = {
  id: string;
  label: string;
  object_type: FederatedInternalObjectType;
  version: number;
};

type ExternalVersionOption = {
  id: string;
  label: string;
  artifact_name: string;
  version_label: string;
};

const schema = z.object({
  mode: z.enum(["internal", "external"]),
  item_kind: z.enum(["internal_requirement", "internal_block", "internal_test_case", "baseline_item", "external_artifact_version"]),
  internal_object_id: z.string().optional().default(""),
  external_artifact_version_id: z.string().optional().default(""),
  role_label: z.string().optional().default(""),
  notes: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export function ConfigurationItemForm({
  contextId,
  internalOptions,
  externalVersionOptions,
}: {
  contextId: string;
  internalOptions: InternalOption[];
  externalVersionOptions: ExternalVersionOption[];
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"internal" | "external">("internal");
  const [selectedInternalId, setSelectedInternalId] = useState<string>(internalOptions[0]?.id || "");
  const [selectedExternalVersionId, setSelectedExternalVersionId] = useState<string>(externalVersionOptions[0]?.id || "");
  const selectedInternal = useMemo(() => internalOptions.find((item) => item.id === selectedInternalId) || internalOptions[0], [internalOptions, selectedInternalId]);
  const selectedExternal = useMemo(() => externalVersionOptions.find((item) => item.id === selectedExternalVersionId) || externalVersionOptions[0], [externalVersionOptions, selectedExternalVersionId]);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      mode: "internal",
      item_kind: "internal_requirement",
      internal_object_id: selectedInternal?.id || "",
      external_artifact_version_id: selectedExternal?.id || "",
      role_label: "",
      notes: "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload =
        values.mode === "internal"
          ? {
              item_kind: values.item_kind as ConfigurationItemKind,
              internal_object_type: selectedInternal?.object_type || null,
              internal_object_id: values.internal_object_id,
              internal_object_version: selectedInternal?.version || null,
              role_label: values.role_label || null,
              notes: values.notes || null,
            }
          : {
              item_kind: "external_artifact_version" as ConfigurationItemKind,
              external_artifact_version_id: values.external_artifact_version_id,
              role_label: values.role_label || null,
              notes: values.notes || null,
            };
      await api.createConfigurationContextItem(contextId, payload);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save configuration item");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant={mode === "internal" ? "primary" : "secondary"} onClick={() => { setMode("internal"); form.setValue("mode", "internal"); }}>
          Internal item
        </Button>
        <Button type="button" variant={mode === "external" ? "primary" : "secondary"} onClick={() => { setMode("external"); form.setValue("mode", "external"); }}>
          External version
        </Button>
      </div>

      {mode === "internal" ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Select {...form.register("item_kind")}>
              <option value="internal_requirement">internal_requirement</option>
              <option value="internal_block">internal_block</option>
              <option value="internal_test_case">internal_test_case</option>
              <option value="baseline_item">baseline_item</option>
            </Select>
            <Select
              {...form.register("internal_object_id", {
                onChange: (event) => {
                  setSelectedInternalId(event.target.value);
                },
              })}
            >
              {internalOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label} / v{option.version}
                </option>
              ))}
            </Select>
          </div>
          <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
            Selected internal object: {selectedInternal?.label || "none"}
          </div>
        </>
      ) : (
        <Select
          {...form.register("external_artifact_version_id", {
            onChange: (event) => {
              setSelectedExternalVersionId(event.target.value);
            },
          })}
        >
          {externalVersionOptions.map((option) => (
            <option key={option.id} value={option.id}>
              {option.artifact_name} - {option.version_label}
            </option>
          ))}
        </Select>
      )}

      <Input placeholder="Role label" {...form.register("role_label")} />
      <Textarea placeholder="Notes" rows={3} {...form.register("notes")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Add context item</Button>
    </form>
  );
}
