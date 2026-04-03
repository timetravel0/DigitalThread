"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { ConnectorDefinition } from "@/lib/types";

const schema = z.object({
  project_id: z.string().min(1),
  name: z.string().min(1),
  connector_type: z.enum(["doors", "sysml", "plm", "simulation", "test", "telemetry", "custom"]),
  base_url: z.string().optional().default(""),
  description: z.string().optional().default(""),
  is_active: z.enum(["true", "false"]),
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

export function ConnectorForm({ initial }: { initial?: Partial<ConnectorDefinition> }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      name: initial?.name || "",
      connector_type: initial?.connector_type || "custom",
      base_url: initial?.base_url || "",
      description: initial?.description || "",
      is_active: initial?.is_active === false ? "false" : "true",
      metadata_json: toJsonText(initial?.metadata_json),
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const payload = {
        ...values,
        is_active: values.is_active === "true",
        metadata_json: values.metadata_json?.trim() ? JSON.parse(values.metadata_json) : {},
      };
      if (initial?.id) {
        await api.updateConnector(initial.id, payload);
        router.push(`/connectors/${initial.id}`);
      } else {
        const created = await api.createConnector(payload);
        router.push(`/connectors/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save connector");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder="Connector name" {...form.register("name")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("connector_type")}>
          <option value="doors">doors</option>
          <option value="sysml">sysml</option>
          <option value="plm">plm</option>
          <option value="simulation">simulation</option>
          <option value="test">test</option>
          <option value="telemetry">telemetry</option>
          <option value="custom">custom</option>
        </Select>
        <Select {...form.register("is_active")}>
          <option value="true">active</option>
          <option value="false">inactive</option>
        </Select>
      </div>
      <Input placeholder="Base URL" {...form.register("base_url")} />
      <Textarea placeholder="Description" rows={3} {...form.register("description")} />
      <Textarea placeholder="Metadata JSON" rows={5} {...form.register("metadata_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Save connector</Button>
    </form>
  );
}
