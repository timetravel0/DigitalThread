"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { DomainProfile } from "@/lib/labels";
import type { ConnectorDefinition, ExternalArtifact } from "@/lib/types";

type ProjectOption = {
  id: string;
  code: string;
  name: string;
  domain_profile: DomainProfile;
};

const schema = z.object({
  project_id: z.string().min(1),
  connector_definition_id: z.string().optional().default(""),
  external_id: z.string().min(1),
  artifact_type: z.enum(["requirement", "sysml_element", "block", "cad_part", "software_module", "test_case", "simulation_model", "test_result", "telemetry_source", "document", "other"]),
  name: z.string().min(1),
  description: z.string().optional().default(""),
  canonical_uri: z.string().optional().default(""),
  native_tool_url: z.string().optional().default(""),
  status: z.enum(["active", "deprecated", "obsolete"]),
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

export function ExternalArtifactForm({ initial, connectors, projects = [], initialProjectId }: { initial?: Partial<ExternalArtifact>; connectors: ConnectorDefinition[]; projects?: ProjectOption[]; initialProjectId?: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [connectorOptions, setConnectorOptions] = useState(connectors);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || initialProjectId || projects[0]?.id || "",
      connector_definition_id: initial?.connector_definition_id || "",
      external_id: initial?.external_id || "",
      artifact_type: initial?.artifact_type || "requirement",
      name: initial?.name || "",
      description: initial?.description || "",
      canonical_uri: initial?.canonical_uri || "",
      native_tool_url: initial?.native_tool_url || "",
      status: initial?.status || "active",
      metadata_json: toJsonText(initial?.metadata_json),
    },
  });
  const selectedProjectId = useWatch({ control: form.control, name: "project_id" });

  useEffect(() => {
    let active = true;
    const load = async () => {
      if (!selectedProjectId) return;
      try {
        const next = await api.connectors(selectedProjectId);
        if (active) setConnectorOptions(next);
      } catch {
        if (active) setConnectorOptions([]);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [selectedProjectId]);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        ...values,
        connector_definition_id: values.connector_definition_id || null,
        canonical_uri: values.canonical_uri || null,
        native_tool_url: values.native_tool_url || null,
        description: values.description || null,
        metadata_json: values.metadata_json?.trim() ? JSON.parse(values.metadata_json) : {},
      };
      if (initial?.id) {
        await api.updateExternalArtifact(initial.id, payload);
        router.push(`/external-artifacts/${initial.id}`);
      } else {
        const created = await api.createExternalArtifact(payload);
        router.push(`/external-artifacts/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save external artifact");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("project_id")} disabled={!projects.length}>
          {(projects.length ? projects : projects[0] ? [projects[0]] : []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.code} - {project.name}
            </option>
          ))}
        </Select>
        <Input placeholder="External ID" {...form.register("external_id")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("connector_definition_id")}>
          <option value="">No connector</option>
          {connectorOptions.map((connector) => (
            <option key={connector.id} value={connector.id}>
              {connector.name} ({connector.connector_type})
            </option>
          ))}
        </Select>
        <Select {...form.register("artifact_type")}>
          <option value="requirement">requirement</option>
          <option value="sysml_element">sysml_element</option>
          <option value="block">block</option>
          <option value="cad_part">cad_part</option>
          <option value="software_module">software_module</option>
          <option value="test_case">test_case</option>
          <option value="simulation_model">simulation_model</option>
          <option value="test_result">test_result</option>
          <option value="telemetry_source">telemetry_source</option>
          <option value="document">document</option>
          <option value="other">other</option>
        </Select>
      </div>
      <Input placeholder="External artifact name" {...form.register("name")} />
      <Textarea placeholder="Description" rows={3} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Canonical URI" {...form.register("canonical_uri")} />
        <Input placeholder="Native tool URL" {...form.register("native_tool_url")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("status")}>
          <option value="active">active</option>
          <option value="deprecated">deprecated</option>
          <option value="obsolete">obsolete</option>
        </Select>
      </div>
      <Textarea placeholder="Metadata JSON" rows={5} {...form.register("metadata_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Save external artifact</Button>
    </form>
  );
}
