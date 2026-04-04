import Link from "next/link";
import type { ReactNode } from "react";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import type { OperationalEvidence } from "@/lib/types";

export function OperationalEvidenceCard({
  evidence,
  objectHref,
}: {
  evidence: OperationalEvidence;
  objectHref?: (objectType: string, objectId: string) => string | null;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-semibold">{evidence.title}</div>
            <div className="mt-1 text-xs text-muted">
              {evidence.source_name} · {evidence.source_type}
            </div>
          </div>
          <Badge tone={qualityTone(evidence.quality_status)}>{evidence.quality_status}</Badge>
        </div>
      </CardHeader>
      <CardBody className="space-y-3">
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Captured at" value={formatTimestamp(evidence.captured_at)} />
          <Field
            label="Coverage window"
            value={`${formatTimestamp(evidence.coverage_window_start)} → ${formatTimestamp(evidence.coverage_window_end)}`}
          />
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Source type" value={evidence.source_type} />
          <Field label="Quality status" value={evidence.quality_status} />
        </div>
        <Block label="Observations summary" value={evidence.observations_summary || "Not provided"} />
        {Object.keys(evidence.aggregated_observations_json || {}).length ? (
          <Block label="Aggregated observations" value={<pre className="whitespace-pre-wrap text-xs text-muted">{JSON.stringify(evidence.aggregated_observations_json, null, 2)}</pre>} />
        ) : null}
        {Object.keys(evidence.derived_metrics_json || {}).length ? (
          <Block label="Derived metrics" value={<pre className="whitespace-pre-wrap text-xs text-muted">{JSON.stringify(evidence.derived_metrics_json, null, 2)}</pre>} />
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

function qualityTone(status: string) {
  if (status === "good") return "success";
  if (status === "poor") return "danger";
  if (status === "warning") return "warning";
  return "neutral";
}

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}
