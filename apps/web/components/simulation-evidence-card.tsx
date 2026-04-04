import Link from "next/link";
import type { ReactNode } from "react";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import type { SimulationEvidence } from "@/lib/types";

export function SimulationEvidenceCard({
  evidence,
  objectHref,
}: {
  evidence: SimulationEvidence;
  objectHref?: (objectType: string, objectId: string) => string | null;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-semibold">{evidence.title}</div>
            <div className="mt-1 text-xs text-muted">
              {evidence.model_reference} - {evidence.scenario_name}
            </div>
          </div>
          <Badge tone={tone(evidence.result)}>{evidence.result}</Badge>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Execution timestamp" value={formatTimestamp(evidence.execution_timestamp)} />
          <Field label="Input summary" value={evidence.input_summary || "Not provided"} />
        </div>
        {evidence.fmi_contract_id ? (
          <div className="rounded-xl border border-line bg-panel2 p-3">
            <div className="text-xs uppercase tracking-[0.2em] text-muted">FMI contract</div>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
              <span className="font-medium">{evidence.fmi_contract_key || evidence.fmi_contract_name || evidence.model_reference}</span>
              {evidence.fmi_contract_model_identifier ? <span className="text-muted">· {evidence.fmi_contract_model_identifier}</span> : null}
              {evidence.fmi_contract_model_version ? <span className="text-muted">· v{evidence.fmi_contract_model_version}</span> : null}
              {objectHref?.("fmi_contract", evidence.fmi_contract_id) ? (
                <Link href={objectHref("fmi_contract", evidence.fmi_contract_id) as string} className="text-accent">Open</Link>
              ) : null}
            </div>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-2">
          <Block label="Expected behavior" value={evidence.expected_behavior || "Not provided"} />
          <Block label="Observed behavior" value={evidence.observed_behavior || "Not provided"} />
        </div>
        {Object.keys(evidence.inputs_json || {}).length ? (
          <Block label="Inputs" value={<pre className="whitespace-pre-wrap text-xs text-muted">{JSON.stringify(evidence.inputs_json, null, 2)}</pre>} />
        ) : null}
        {Object.keys(evidence.metadata_json || {}).length ? (
          <Block label="Metadata" value={<pre className="whitespace-pre-wrap text-xs text-muted">{JSON.stringify(evidence.metadata_json, null, 2)}</pre>} />
        ) : null}
        {evidence.linked_objects?.length ? (
          <div className="flex flex-wrap gap-2">
            {evidence.linked_objects.map((object) => {
              const href = objectHref?.(object.object_type, object.object_id) || null;
              const chip = (
                <span className="inline-flex items-center rounded-full border border-line bg-white/5 px-2 py-1 text-xs text-text">
                  {object.label}
                </span>
              );
              return href ? (
                <Link key={`${object.object_type}-${object.object_id}`} href={href}>
                  {chip}
                </Link>
              ) : (
                <span key={`${object.object_type}-${object.object_id}`}>{chip}</span>
              );
            })}
          </div>
        ) : null}
      </CardBody>
    </Card>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 text-sm text-text">{value}</div>
    </div>
  );
}

function Block({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-sm text-text">{value}</div>
    </div>
  );
}

function tone(result: string) {
  if (result === "passed") return "success";
  if (result === "failed") return "danger";
  return "warning";
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

