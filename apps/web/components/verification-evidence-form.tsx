"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { VerificationEvidenceType } from "@/lib/types";

const schema = z.object({
  title: z.string().min(1),
  evidence_type: z.enum(["test_result", "simulation", "telemetry", "analysis", "inspection", "other"]),
  summary: z.string().optional().default(""),
  observed_at: z.string().optional().default(""),
  source_name: z.string().optional().default(""),
  source_reference: z.string().optional().default(""),
  simulation_model: z.string().optional().default(""),
  simulation_scenario: z.string().optional().default(""),
  simulation_inputs_json: z.string().optional().default(""),
  simulation_outputs_json: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export function VerificationEvidenceForm({
  projectId,
  subjectType,
  subjectId,
  subjectLabel,
}: {
  projectId: string;
  subjectType: "requirement" | "test_case" | "component" | "non_conformity";
  subjectId: string;
  subjectLabel: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      evidence_type: "analysis",
      summary: "",
      observed_at: "",
      source_name: "",
      source_reference: "",
      simulation_model: "",
      simulation_scenario: "",
      simulation_inputs_json: "",
      simulation_outputs_json: "",
    },
  });
  const evidenceType = form.watch("evidence_type");

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const parseJson = (raw: string | undefined, label: string) => {
        if (!raw?.trim()) return null;
        try {
          return JSON.parse(raw);
        } catch {
          throw new Error(`${label} must be valid JSON.`);
        }
      };
      const metadata_json = values.evidence_type === "simulation"
        ? {
            simulation: {
              model: values.simulation_model || null,
              scenario: values.simulation_scenario || null,
              inputs: parseJson(values.simulation_inputs_json, "Simulation inputs"),
              outputs: parseJson(values.simulation_outputs_json, "Simulation outputs"),
            },
          }
        : {};
      await api.createVerificationEvidence(projectId, {
        project_id: projectId,
        title: values.title,
        evidence_type: values.evidence_type as VerificationEvidenceType,
        summary: values.summary || "",
        observed_at: values.observed_at ? new Date(values.observed_at).toISOString() : null,
        source_name: values.source_name || null,
        source_reference: values.source_reference || null,
        metadata_json,
        ...(subjectType === "requirement"
          ? { linked_requirement_ids: [subjectId], linked_test_case_ids: [] }
          : subjectType === "test_case"
            ? { linked_requirement_ids: [], linked_test_case_ids: [subjectId] }
            : subjectType === "component"
              ? { linked_requirement_ids: [], linked_test_case_ids: [], linked_component_ids: [subjectId] }
              : { linked_requirement_ids: [], linked_test_case_ids: [], linked_component_ids: [], linked_non_conformity_ids: [subjectId] }),
      });
      router.refresh();
      form.reset({
        title: "",
        evidence_type: "analysis",
        summary: "",
        observed_at: "",
        source_name: "",
        source_reference: "",
        simulation_model: "",
        simulation_scenario: "",
        simulation_inputs_json: "",
        simulation_outputs_json: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save verification evidence");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="rounded-xl border border-line bg-panel2 p-3 text-sm">
        <div className="text-xs uppercase tracking-[0.2em] text-muted">Linked subject</div>
        <div className="mt-1 font-medium">{subjectLabel}</div>
        <div className="text-xs text-muted">{subjectType}</div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Evidence title" {...form.register("title")} />
        <Select {...form.register("evidence_type")}>
          <option value="analysis">analysis</option>
          <option value="inspection">inspection</option>
          <option value="test_result">test_result</option>
          <option value="simulation">simulation</option>
          <option value="telemetry">telemetry</option>
          <option value="other">other</option>
        </Select>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input type="datetime-local" {...form.register("observed_at")} />
        <Input placeholder="Source name" {...form.register("source_name")} />
      </div>
      <Input placeholder="Source reference" {...form.register("source_reference")} />
      <Textarea placeholder="Evidence summary" rows={3} {...form.register("summary")} />
      {evidenceType === "simulation" ? (
        <div className="space-y-4 rounded-xl border border-line bg-panel2 p-4">
          <div className="text-xs uppercase tracking-[0.2em] text-muted">Simulation details</div>
          <Input placeholder="Simulation model" {...form.register("simulation_model")} />
          <Input placeholder="Simulation scenario" {...form.register("simulation_scenario")} />
          <Textarea placeholder='Simulation inputs JSON, e.g. {"airspeed": 17}' rows={4} {...form.register("simulation_inputs_json")} />
          <Textarea placeholder='Simulation outputs JSON, e.g. {"max_temperature": 41.2}' rows={4} {...form.register("simulation_outputs_json")} />
        </div>
      ) : null}
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Add verification evidence</Button>
    </form>
  );
}
