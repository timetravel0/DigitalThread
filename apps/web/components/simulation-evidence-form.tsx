"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Badge, Button, Input, Select, Textarea } from "@/components/ui";
import { FormFooter, JsonTextareaField, InlineHelp } from "@/components/form-helpers";

const schema = z.object({
  title: z.string().min(1, "Title is required"),
  model_reference: z.string().min(1, "Model reference is required"),
  scenario_name: z.string().min(1, "Scenario name is required"),
  input_summary: z.string().optional().default(""),
  execution_timestamp: z.string().min(1, "Execution timestamp is required"),
  result: z.enum(["passed", "failed", "partial"]),
  expected_behavior: z.string().min(1, "Expected behavior is required"),
  observed_behavior: z.string().min(1, "Observed behavior is required"),
  inputs_json: z.string().optional().default("{}"),
  metadata_json: z.string().optional().default("{}"),
  linked_requirement_id: z.string().optional().default(""),
  linked_test_case_id: z.string().optional().default(""),
  linked_verification_evidence_id: z.string().optional().default(""),
  fmi_contract_id: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

type Option = { id: string; label: string };

export function SimulationEvidenceForm({
  projectId,
  linkedRequirementIds = [],
  linkedTestCaseIds = [],
  linkedVerificationEvidenceIds = [],
  fmiContractOptions = [],
  requirementOptions = [],
  testCaseOptions = [],
  verificationEvidenceOptions = [],
  lockedSubjectLabel,
}: {
  projectId: string;
  linkedRequirementIds?: string[];
  linkedTestCaseIds?: string[];
  linkedVerificationEvidenceIds?: string[];
  fmiContractOptions?: Option[];
  requirementOptions?: Option[];
  testCaseOptions?: Option[];
  verificationEvidenceOptions?: Option[];
  lockedSubjectLabel?: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: "",
      model_reference: "",
      scenario_name: "",
      input_summary: "",
      execution_timestamp: toDatetimeLocal(new Date()),
      result: "passed",
      expected_behavior: "",
      observed_behavior: "",
      inputs_json: "{}",
      metadata_json: "{}",
      linked_requirement_id: "",
      linked_test_case_id: "",
      linked_verification_evidence_id: "",
      fmi_contract_id: "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        project_id: projectId,
        title: values.title,
        model_reference: values.model_reference,
        scenario_name: values.scenario_name,
        input_summary: values.input_summary || null,
        execution_timestamp: new Date(values.execution_timestamp).toISOString(),
        result: values.result,
        expected_behavior: values.expected_behavior,
        observed_behavior: values.observed_behavior,
        inputs_json: parseJson(values.inputs_json, "Simulation inputs"),
        metadata_json: parseJson(values.metadata_json, "Simulation metadata"),
        linked_requirement_ids: unique([...linkedRequirementIds, ...(values.linked_requirement_id ? [values.linked_requirement_id] : [])]),
        linked_test_case_ids: unique([...linkedTestCaseIds, ...(values.linked_test_case_id ? [values.linked_test_case_id] : [])]),
        linked_verification_evidence_ids: unique([
          ...linkedVerificationEvidenceIds,
          ...(values.linked_verification_evidence_id ? [values.linked_verification_evidence_id] : []),
        ]),
        fmi_contract_id: values.fmi_contract_id || null,
      };
      await api.createSimulationEvidence(projectId, payload);
      router.refresh();
      form.reset({
        title: "",
        model_reference: "",
        scenario_name: "",
        input_summary: "",
        execution_timestamp: toDatetimeLocal(new Date()),
        result: "passed",
        expected_behavior: "",
        observed_behavior: "",
        inputs_json: "{}",
        metadata_json: "{}",
        linked_requirement_id: "",
        linked_test_case_id: "",
        linked_verification_evidence_id: "",
        fmi_contract_id: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save simulation evidence");
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
      {linkedRequirementIds.length || linkedTestCaseIds.length || linkedVerificationEvidenceIds.length ? (
        <div className="rounded-xl border border-line bg-panel2 p-3 text-xs text-muted">
          <div className="mb-2 font-medium text-text">Already linked</div>
          <div className="flex flex-wrap gap-2">
            {linkedRequirementIds.map((id) => <Badge key={id}>requirement: {short(id)}</Badge>)}
            {linkedTestCaseIds.map((id) => <Badge key={id}>test_case: {short(id)}</Badge>)}
            {linkedVerificationEvidenceIds.map((id) => <Badge key={id}>verification_evidence: {short(id)}</Badge>)}
          </div>
        </div>
      ) : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Title" {...form.register("title")} />
        <Input placeholder="Model reference" {...form.register("model_reference")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Scenario name" {...form.register("scenario_name")} />
        <Input type="datetime-local" {...form.register("execution_timestamp")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("result")}>
          <option value="passed">passed</option>
          <option value="partial">partial</option>
          <option value="failed">failed</option>
        </Select>
        <Input placeholder="Input summary" {...form.register("input_summary")} />
      </div>
      <Textarea placeholder="Expected behavior" rows={3} {...form.register("expected_behavior")} />
      <Textarea placeholder="Observed behavior" rows={3} {...form.register("observed_behavior")} />
      <JsonTextareaField
        label="Simulation inputs"
        description="Capture the input set that makes this scenario reproducible."
        example='{"ambient_low_c": -6, "payload_kg": 1.2}'
        rows={4}
        {...form.register("inputs_json")}
      />
      <JsonTextareaField
        label="Simulation metadata"
        description="Use this for contract references, environment notes, or tool-specific context."
        example='{"contract_reference": "FMI-placeholder:THERMAL-ENVELOPE"}'
        rows={4}
        {...form.register("metadata_json")}
      />
      <div className="grid gap-4 md:grid-cols-3">
        <Select {...form.register("linked_requirement_id")}>
          <option value="">Optional requirement</option>
          {requirementOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </Select>
        <Select {...form.register("linked_test_case_id")}>
          <option value="">Optional test case</option>
          {testCaseOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </Select>
        <Select {...form.register("linked_verification_evidence_id")}>
          <option value="">Optional verification evidence</option>
          {verificationEvidenceOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
        </Select>
      </div>
      <Select {...form.register("fmi_contract_id")}>
        <option value="">Optional FMI contract</option>
        {fmiContractOptions.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
      </Select>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <FormFooter submitLabel="Add simulation evidence" onCancel={() => router.back()} />
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

