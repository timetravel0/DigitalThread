"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { Block } from "@/lib/types";

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  name: z.string().min(1),
  description: z.string().optional().default(""),
  block_kind: z.enum(["system", "subsystem", "assembly", "component", "software", "interface", "other"]),
  abstraction_level: z.enum(["logical", "physical"]),
  status: z.enum(["draft", "in_review", "approved", "rejected", "obsolete"]),
  owner: z.string().optional().default(""),
});

type FormValues = z.infer<typeof schema>;

export function BlockForm({ initial }: { initial?: Partial<Block> }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      name: initial?.name || "",
      description: initial?.description || "",
      block_kind: initial?.block_kind || "system",
      abstraction_level: initial?.abstraction_level || "logical",
      status: initial?.status || "draft",
      owner: initial?.owner || "",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      if (initial?.id) {
        await api.updateBlock(initial.id, values);
        router.push(`/blocks/${initial.id}`);
      } else {
        const created = await api.createBlock(values);
        router.push(`/blocks/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save block");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder="Block key" {...form.register("key")} />
      </div>
      <Input placeholder="Block name" {...form.register("name")} />
      <Textarea placeholder="Description" rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("block_kind")}>
          <option value="system">system</option>
          <option value="subsystem">subsystem</option>
          <option value="assembly">assembly</option>
          <option value="component">component</option>
          <option value="software">software</option>
          <option value="interface">interface</option>
          <option value="other">other</option>
        </Select>
        <Select {...form.register("abstraction_level")}>
          <option value="logical">logical</option>
          <option value="physical">physical</option>
        </Select>
        <Select {...form.register("status")}>
          <option value="draft">draft</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="obsolete">obsolete</option>
        </Select>
        <Input placeholder="Owner" {...form.register("owner")} />
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Save block</Button>
    </form>
  );
}
