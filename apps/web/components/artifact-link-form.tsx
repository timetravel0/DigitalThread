"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { ArtifactLink, ExternalArtifact, FederatedInternalObjectType } from "@/lib/types";

const schema = z.object({
  project_id: z.string().min(1),
  external_artifact_id: z.string().min(1),
  external_artifact_version_id: z.string().optional().default(""),
  relation_type: z.enum(["authoritative_reference", "derived_from_external", "synchronized_with", "validated_against", "exported_to", "maps_to"]),
  rationale: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export function ArtifactLinkForm({
  projectId,
  internalObjectType,
  internalObjectId,
  internalObjectLabel,
  artifacts,
}: {
  projectId: string;
  internalObjectType: FederatedInternalObjectType;
  internalObjectId: string;
  internalObjectLabel: string;
  artifacts: ExternalArtifact[];
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>(artifacts[0]?.id || "");
  const selectedArtifact = useMemo(() => artifacts.find((artifact) => artifact.id === selectedArtifactId) || artifacts[0], [artifacts, selectedArtifactId]);
  const versions = selectedArtifact?.versions || [];
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: projectId,
      external_artifact_id: selectedArtifact?.id || "",
      external_artifact_version_id: selectedArtifact?.versions?.[0]?.id || "",
      relation_type: "maps_to",
      rationale: "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        project_id: projectId,
        internal_object_type: internalObjectType,
        internal_object_id: internalObjectId,
        external_artifact_id: values.external_artifact_id,
        external_artifact_version_id: values.external_artifact_version_id || null,
        relation_type: values.relation_type,
        rationale: values.rationale || null,
      };
      await api.createArtifactLink(projectId, payload);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save artifact link");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="rounded-xl border border-line bg-panel2 p-3 text-sm">
        <div className="text-xs uppercase tracking-[0.2em] text-muted">Internal object</div>
        <div className="mt-1 font-medium">{internalObjectLabel}</div>
        <div className="text-xs text-muted">{internalObjectType}</div>
      </div>
      {artifacts.length ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Select
              {...form.register("external_artifact_id", {
                onChange: (event) => {
                  const nextId = event.target.value;
                  setSelectedArtifactId(nextId);
                  const nextArtifact = artifacts.find((artifact) => artifact.id === nextId);
                  form.setValue("external_artifact_version_id", nextArtifact?.versions?.[0]?.id || "");
                },
              })}
            >
              {artifacts.map((artifact) => (
                <option key={artifact.id} value={artifact.id}>
                  {artifact.external_id} - {artifact.name}
                </option>
              ))}
            </Select>
            <Select {...form.register("relation_type")}>
              <option value="maps_to">maps_to</option>
              <option value="authoritative_reference">authoritative_reference</option>
              <option value="validated_against">validated_against</option>
              <option value="derived_from_external">derived_from_external</option>
              <option value="synchronized_with">synchronized_with</option>
              <option value="exported_to">exported_to</option>
            </Select>
          </div>
          <Select {...form.register("external_artifact_version_id")}>
            {versions.length ? (
              versions.map((version) => (
                <option key={version.id} value={version.id}>
                  {version.version_label}{version.revision_label ? ` / ${version.revision_label}` : ""}
                </option>
              ))
            ) : (
              <option value="">No versions available</option>
            )}
          </Select>
        </>
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
          No external artifacts are available in this project yet.
        </div>
      )}
      <Textarea placeholder="Rationale" rows={3} {...form.register("rationale")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit" disabled={!artifacts.length}>Link external source</Button>
    </form>
  );
}
