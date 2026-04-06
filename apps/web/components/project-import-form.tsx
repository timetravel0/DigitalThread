"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import type { ProjectImportFormat, ProjectImportResponse } from "@/lib/types";
import { Button, Card, CardBody, Input, Select, Textarea } from "@/components/ui";
import { FormFooter, InlineHelp } from "@/components/form-helpers";

const schema = z.object({
  format: z.enum(["json", "csv"]),
  content: z.string().min(1, "Import content is required."),
});

type FormValues = z.infer<typeof schema>;

function short(value: string) {
  return value.length > 12 ? `${value.slice(0, 12)}...` : value;
}

export function ProjectImportForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProjectImportResponse | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      format: "json",
      content: `{
  "external_artifacts": [
    {
      "record_type": "external_artifact",
      "external_id": "EXT-REQ-001",
      "artifact_type": "requirement",
      "name": "Imported requirement pointer",
      "description": "Example external requirement reference",
      "status": "active"
    }
  ]
}`,
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    setResult(null);
    try {
      const created = await api.importProjectRecords(projectId, {
        format: values.format as ProjectImportFormat,
        content: values.content,
      });
      setResult(created);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to import records");
    }
  });

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <Select {...form.register("format")}>
            <option value="json">json</option>
            <option value="csv">csv</option>
          </Select>
          <Input value={projectId} readOnly className="bg-slate-950/60" />
        </div>
        <Textarea rows={18} placeholder="Paste JSON or CSV content here" {...form.register("content")} />
        <InlineHelp>
          JSON supports `external_artifacts` and `verification_evidence` arrays. CSV supports a `record_type` column with one record per row.
        </InlineHelp>
        {error ? <div className="text-sm text-danger">{error}</div> : null}
        <FormFooter submitLabel="Import records" onCancel={() => router.back()} />
      </form>

      <Card>
        <CardBody className="space-y-4">
          <div>
            <div className="text-sm font-semibold text-text">Import contract</div>
            <div className="mt-1 text-sm text-muted">
              Use JSON with `external_artifacts` and `verification_evidence` arrays, or CSV rows with a `record_type` column.
            </div>
          </div>
          {result ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <Stat label="Parsed records" value={result.summary.parsed_records} />
                <Stat label="External artifacts" value={result.summary.created_external_artifacts} />
                <Stat label="Verification evidence" value={result.summary.created_verification_evidence} />
              </div>
              {result.warnings.length ? (
                <div className="rounded-xl border border-yellow-400/30 bg-yellow-400/10 p-3 text-sm text-yellow-100">
                  {result.warnings.map((warning) => <div key={warning}>{warning}</div>)}
                </div>
              ) : null}
              {result.external_artifacts.length ? (
                <div className="space-y-2">
                  <div className="text-sm font-semibold">Imported external artifacts</div>
                  <div className="flex flex-wrap gap-2">
                    {result.external_artifacts.map((artifact) => (
                      <Button key={artifact.id} href={`/external-artifacts/${artifact.id}`} variant="secondary">
                        {short(artifact.external_id)}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : null}
              {result.verification_evidence.length ? (
                <div className="space-y-2">
                  <div className="text-sm font-semibold">Imported verification evidence</div>
                  <div className="flex flex-wrap gap-2">
                    {result.verification_evidence.map((evidence) => (
                      <Button key={evidence.id} href={`/verification-evidence/${evidence.id}`} variant="secondary">
                        {short(evidence.title)}
                      </Button>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-sm text-muted">Submit an import to see the created records and links here.</div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-text">{value}</div>
    </div>
  );
}
