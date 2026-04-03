"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { ConfigurationContext } from "@/lib/types";

const schema = z.object({
  project_id: z.string().min(1),
  key: z.string().min(1),
  name: z.string().min(1),
  description: z.string().optional().default(""),
  context_type: z.enum(["working", "baseline_candidate", "review_gate", "released", "imported"]),
  status: z.enum(["draft", "active", "frozen", "obsolete"]),
});

type FormValues = z.infer<typeof schema>;

export function ConfigurationContextForm({ initial }: { initial?: Partial<ConfigurationContext> }) {
  const isLocked = initial?.status === "frozen" || initial?.context_type === "released";
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      name: initial?.name || "",
      description: initial?.description || "",
      context_type: initial?.context_type || "working",
      status: initial?.status || "draft",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    if (isLocked) {
      setError("This configuration context is frozen or released and cannot be edited.");
      return;
    }
    try {
      if (initial?.id) {
        await api.updateConfigurationContext(initial.id, values);
        router.push(`/configuration-contexts/${initial.id}`);
      } else {
        const created = await api.createConfigurationContext(values);
        router.push(`/configuration-contexts/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save configuration context");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      {isLocked ? <div className="rounded-xl border border-warning/30 bg-warning/10 p-4 text-sm text-warning">This configuration context is frozen or released and cannot be edited in place.</div> : null}
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" disabled={isLocked} {...form.register("project_id")} />
        <Input placeholder="Context key" disabled={isLocked} {...form.register("key")} />
      </div>
      <Input placeholder="Context name" disabled={isLocked} {...form.register("name")} />
      <Textarea placeholder="Description" rows={3} disabled={isLocked} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select disabled={isLocked} {...form.register("context_type")}>
          <option value="working">working</option>
          <option value="baseline_candidate">baseline_candidate</option>
          <option value="review_gate">review_gate</option>
          <option value="released">released</option>
          <option value="imported">imported</option>
        </Select>
        <Select disabled={isLocked} {...form.register("status")}>
          <option value="draft">draft</option>
          <option value="active">active</option>
          <option value="frozen">frozen</option>
          <option value="obsolete">obsolete</option>
        </Select>
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit" disabled={isLocked}>Save context</Button>
    </form>
  );
}
