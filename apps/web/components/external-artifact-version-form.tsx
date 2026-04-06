"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Textarea } from "@/components/ui";
import type { ExternalArtifactVersion } from "@/lib/types";
import { FormFooter, JsonTextareaField } from "@/components/form-helpers";

const schema = z.object({
  version_label: z.string().min(1),
  revision_label: z.string().optional().default(""),
  checksum_or_signature: z.string().optional().default(""),
  effective_date: z.string().optional().default(""),
  source_timestamp: z.string().optional().default(""),
  metadata_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

function toJsonText(value: unknown) {
  if (!value) return "{}";
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "{}";
  }
}

function toDateInput(value?: string | null) {
  return value ? value.slice(0, 10) : "";
}

function toDateTimeInput(value?: string | null) {
  return value ? value.slice(0, 16) : "";
}

export function ExternalArtifactVersionForm({ artifactId, initial }: { artifactId: string; initial?: Partial<ExternalArtifactVersion> }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      version_label: initial?.version_label || "",
      revision_label: initial?.revision_label || "",
      checksum_or_signature: initial?.checksum_or_signature || "",
      effective_date: toDateInput(initial?.effective_date),
      source_timestamp: toDateTimeInput(initial?.source_timestamp),
      metadata_json: toJsonText(initial?.metadata_json),
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        version_label: values.version_label,
        revision_label: values.revision_label || null,
        checksum_or_signature: values.checksum_or_signature || null,
        effective_date: values.effective_date || null,
        source_timestamp: values.source_timestamp ? `${values.source_timestamp}:00Z` : null,
        metadata_json: values.metadata_json?.trim() ? JSON.parse(values.metadata_json) : {},
      };
      await api.createExternalArtifactVersion(artifactId, payload);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save artifact version");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Version label" {...form.register("version_label")} />
        <Input placeholder="Revision label" {...form.register("revision_label")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Checksum or signature" {...form.register("checksum_or_signature")} />
        <Input type="date" placeholder="Effective date" {...form.register("effective_date")} />
      </div>
      <Input type="datetime-local" placeholder="Source timestamp" {...form.register("source_timestamp")} />
      <JsonTextareaField
        label="Version metadata"
        description="Use this to capture checksum details, release notes, or provenance fields that do not fit the fixed columns."
        example='{"checksum_algorithm": "sha256", "release_note": "Initial pinned version"}'
        rows={4}
        {...form.register("metadata_json")}
      />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <FormFooter submitLabel="Add version" onCancel={() => router.back()} />
    </form>
  );
}
