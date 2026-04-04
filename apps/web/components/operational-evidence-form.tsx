"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Badge, Button, Input, Select, Textarea } from "@/components/ui";

const schema = z.object({
  title: z.string().min(1, "Title is required"),
  source_name: z.string().min(1, "Source name is required"),
  source_type: z.enum(["sensor", "system"]),
  captured_at: z.string().min(1, "Captured time is required"),
  coverage_window_start: z.string().min(1, "Coverage window start is required"),
  coverage_window_end: z.string().min(1, "Coverage window end is required"),
  observations_summary: z.string().optional().default(""),
  quality_status: z.enum(["good", "warning", "poor", "unknown"]),
  aggregated_observations_json: z.string().optional().default("{}"),
  derived_metrics_json: z.string().optional().default("{}"),
  metadata_json: z.string().optional().default("{}"),
  linked_requirement_id: z.string().optional().default(""),
  linked_verification_evidence_id: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;
type Option = { id: string; label: string };

export function OperationalEvidenceForm({
  projectId,
  linkedRequirementIds = [],
  linkedVerificationEvidenceIds = [],
  requirementOptions = [],
  verificationEvidenceOptions = [],
  lockedSubjectLabel,
}: {
  projectId: string;
  linkedRequirementIds?: string[];
  linkedVerificationEvidenceIds?: string[];
  requirementOptions?: Option[];
  verificationEvidenceOptions?: Option[];
  lockedSubjectLabel?: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      source_name: "",
      source_type: "system",
      captured_at: toDatetimeLocal(new Date()),
      coverage_window_start: toDatetimeLocal(new Date(Date.now() - 30 * 60 * 1000)),
      coverage_window_end: toDatetimeLocal(new Date()),
      observations_summary: "",
      quality_status: "warning",
      aggregated_observations_json: "{}",
      derived_metrics_json: "{}",
      metadata_json: "{}",
      linked_requirement_id: "",
      linked_verification_evidence_id: "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        project_id: projectId,
        title: values.title,
        source_name: values.source_name,
        source_type: values.source_type,
        captured_at: new Date(values.captured_at).toISOString(),
        coverage_window_start: new Date(values.coverage_window_start).toISOString(),
        coverage_window_end: new Date(values.coverage_window_end).toISOString(),
        observations_summary: values.observations_summary || "",
        quality_status: values.quality_status,
        aggregated_observations_json: parseJson(values.aggregated_observations_json, "Aggregated observations"),
        derived_metrics_json: parseJson(values.derived_metrics_json, "Derived metrics"),
        metadata_json: parseJson(values.metadata_json, "Operational metadata"),
        linked_requirement_ids: unique([...linkedRequirementIds, ...(values.linked_requirement_id ? [values.linked_requirement_id] : [])]),
        linked_verification_evidence_ids: unique([
          ...linkedVerificationEvidenceIds,
          ...(values.linked_verification_evidence_id ? [values.linked_verification_evidence_id] : []),
        ]),
      };
      await api.createOperationalEvidence(projectId, payload);
      router.refresh();
      form.reset({
        title: "",
        source_name: "",
        source_type: "system",
        captured_at: toDatetimeLocal(new Date()),
        coverage_window_start: toDatetimeLocal(new Date(Date.now() - 30 * 60 * 1000)),
        coverage_window_end: toDatetimeLocal(new Date()),
        observations_summary: "",
        quality_status: "warning",
        aggregated_observations_json: "{}",
        derived_metrics_json: "{}",
        metadata_json: "{}",
        linked_requirement_id: "",
        linked_verification_evidence_id: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save operational evidence");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      {lockedSubjectLabel ? (
        <div className="rounded-xl border border-line bg-panel2 p-3 text-sm">
          <div className="text-xs uppercase tracking-[0.2em] text-muted">Primary linked subject</div>
          <div className="mt-1 font-medium">{lockedSubjectLabel}</div>
        </div>
      ) : null}
      {linkedRequirementIds.length || linkedVerificationEvidenceIds.length ? (
        <div className="rounded-xl border border-line bg-panel2 p-3 text-xs text-muted">
          <div className="mb-2 font-medium text-text">Already linked</div>
          <div className="flex flex-wrap gap-2">
            {linkedRequirementIds.map((id) => <Badge key={id}>requirement: {short(id)}</Badge>)}
            {linkedVerificationEvidenceIds.map((id) => <Badge key={id}>verification_evidence: {short(id)}</Badge>)}
          </div>
        </div>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Batch title" {...form.register("title")} />
        <Input placeholder="Source name" {...form.register("source_name")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("source_type")}>
          <option value="system">system</option>
          <option value="sensor">sensor</option>
        </Select>
        <Select {...form.register("quality_status")}>
          <option value="warning">warning</option>
          <option value="good">good</option>
          <option value="poor">poor</option>
          <option value="unknown">unknown</option>
        </Select>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Input type="datetime-local" {...form.register("captured_at")} />
        <Input type="datetime-local" {...form.register("coverage_window_start")} />
        <Input type="datetime-local" {...form.register("coverage_window_end")} />
      </div>
      <Textarea placeholder="Observations summary" rows={3} {...form.register("observations_summary")} />
      <Textarea placeholder='Aggregated observations JSON, e.g. {"duration_minutes": 22}' rows={4} {...form.register("aggregated_observations_json")} />
      <Textarea placeholder='Derived metrics JSON, e.g. {"coverage_minutes": 22}' rows={4} {...form.register("derived_metrics_json")} />
      <Textarea placeholder='Metadata JSON, e.g. {"contract_reference": "OP-EVBATCH:DR-RUN-001"}' rows={4} {...form.register("metadata_json")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("linked_requirement_id")}>
          <option value="">Optional requirement</option>
          {requirementOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </Select>
        <Select {...form.register("linked_verification_evidence_id")}>
          <option value="">Optional verification evidence</option>
          {verificationEvidenceOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </Select>
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Add operational evidence</Button>
    </form>
  );
}

function parseJson(raw: string | undefined, label: string) {
  if (!raw?.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error(`${label} must be valid JSON.`);
  }
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function toDatetimeLocal(date: Date) {
  const pad = (value: number) => String(value).padStart(2, "0");
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hours = pad(date.getHours());
  const minutes = pad(date.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function short(value: string) {
  return value.length > 8 ? `${value.slice(0, 8)}...` : value;
}
