"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { Requirement } from "@/lib/types";

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  title: z.string().min(1),
  description: z.string().optional().default(""),
  category: z.enum(["performance", "safety", "environment", "operations", "compliance"]),
  priority: z.enum(["low", "medium", "high", "critical"]),
  verification_method: z.enum(["analysis", "inspection", "test", "demonstration"]),
  status: z.enum(["draft", "in_review", "approved", "rejected", "implemented", "verified", "failed", "obsolete", "retired"]),
  parent_requirement_id: z.string().optional().or(z.literal("")),
  verification_criteria_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

export function RequirementForm({ initial, onSaved }: { initial?: Partial<Requirement>; onSaved?: () => void }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      title: initial?.title || "",
      description: initial?.description || "",
      category: initial?.category || "performance",
      priority: initial?.priority || "medium",
      verification_method: initial?.verification_method || "test",
      status: initial?.status || "draft",
      parent_requirement_id: initial?.parent_requirement_id || "",
      verification_criteria_json: JSON.stringify(initial?.verification_criteria_json || {}, null, 2),
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const verification_criteria_json = values.verification_criteria_json?.trim()
        ? JSON.parse(values.verification_criteria_json)
        : {};
      if (initial?.id) {
        await api.updateRequirement(initial.id, { ...values, verification_criteria_json });
        onSaved?.();
        router.refresh();
        router.push(`/requirements/${initial.id}`);
      } else {
        const created = await api.createRequirement({ ...values, verification_criteria_json });
        onSaved?.();
        router.push(`/requirements/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save requirement");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder="Requirement key" {...form.register("key")} />
      </div>
      <Input placeholder="Requirement title" {...form.register("title")} />
      <Textarea placeholder="Description" rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("category")}>
          <option value="performance">performance</option>
          <option value="safety">safety</option>
          <option value="environment">environment</option>
          <option value="operations">operations</option>
          <option value="compliance">compliance</option>
        </Select>
        <Select {...form.register("priority")}>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="critical">critical</option>
        </Select>
        <Select {...form.register("verification_method")}>
          <option value="analysis">analysis</option>
          <option value="inspection">inspection</option>
          <option value="test">test</option>
          <option value="demonstration">demonstration</option>
        </Select>
        <Select {...form.register("status")}>
          <option value="draft">draft</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="implemented">implemented</option>
          <option value="verified">verified</option>
          <option value="failed">failed</option>
          <option value="obsolete">obsolete</option>
          <option value="retired">retired</option>
        </Select>
      </div>
      <Input placeholder="Parent requirement ID (optional)" {...form.register("parent_requirement_id")} />
      <Textarea placeholder='Verification criteria JSON, for example {"telemetry_thresholds": {"battery_consumption_pct": {"max": 85}}}' rows={6} {...form.register("verification_criteria_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Save requirement</Button>
    </form>
  );
}
