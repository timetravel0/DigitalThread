"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Textarea } from "@/components/ui";

const schema = z.object({
  key: z.string().min(1, "Key is required"),
  name: z.string().min(1, "Name is required"),
  description: z.string().optional().default(""),
  model_identifier: z.string().min(1, "Model identifier is required"),
  model_version: z.string().optional().default(""),
  model_uri: z.string().optional().default(""),
  adapter_profile: z.string().optional().default(""),
  contract_version: z.string().optional().default("fmi.placeholder.v1"),
  metadata_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

export function FMIContractForm({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      key: "",
      name: "",
      description: "",
      model_identifier: "",
      model_version: "",
      model_uri: "",
      adapter_profile: "",
      contract_version: "fmi.placeholder.v1",
      metadata_json: "{}",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      await api.createFmiContract(projectId, {
        project_id: projectId,
        key: values.key,
        name: values.name,
        description: values.description || "",
        model_identifier: values.model_identifier,
        model_version: values.model_version || null,
        model_uri: values.model_uri || null,
        adapter_profile: values.adapter_profile || null,
        contract_version: values.contract_version || "fmi.placeholder.v1",
        metadata_json: parseJson(values.metadata_json),
      });
      router.refresh();
      form.reset({
        key: "",
        name: "",
        description: "",
        model_identifier: "",
        model_version: "",
        model_uri: "",
        adapter_profile: "",
        contract_version: "fmi.placeholder.v1",
        metadata_json: "{}",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save FMI contract");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Key" {...form.register("key")} />
        <Input placeholder="Name" {...form.register("name")} />
      </div>
      <Input placeholder="Model identifier" {...form.register("model_identifier")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Model version" {...form.register("model_version")} />
        <Input placeholder="Model URI" {...form.register("model_uri")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Adapter profile" {...form.register("adapter_profile")} />
        <Input placeholder="Contract version" {...form.register("contract_version")} />
      </div>
      <Textarea placeholder="Description" rows={3} {...form.register("description")} />
      <Textarea placeholder='Metadata JSON, e.g. {"adapter": "placeholder"}' rows={4} {...form.register("metadata_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Add FMI contract</Button>
    </form>
  );
}

function parseJson(raw: string | undefined) {
  if (!raw?.trim()) return {};
  try {
    return JSON.parse(raw);
  } catch {
    throw new Error("Metadata JSON must be valid JSON.");
  }
}
