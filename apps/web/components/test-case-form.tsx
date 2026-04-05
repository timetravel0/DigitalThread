"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import { getLabels, type DomainProfile, type LabelSet } from "@/lib/labels";
import type { TestCase } from "@/lib/types";

type TestMethodValue = "bench" | "simulation" | "field" | "inspection";

export const TEST_METHOD_OPTIONS: Record<DomainProfile, { value: TestMethodValue; label: string }[]> = {
  engineering: [
    { value: "bench", label: "bench" },
    { value: "simulation", label: "simulation" },
    { value: "field", label: "field" },
    { value: "inspection", label: "inspection" },
  ],
  manufacturing: [
    { value: "bench", label: "production bench" },
    { value: "simulation", label: "virtual test" },
    { value: "field", label: "line trial" },
    { value: "inspection", label: "audit" },
  ],
  personal: [
    { value: "bench", label: "dry run" },
    { value: "simulation", label: "simulation" },
    { value: "field", label: "real-world check" },
    { value: "inspection", label: "inspection" },
  ],
  custom: [
    { value: "bench", label: "bench" },
    { value: "simulation", label: "simulation" },
    { value: "field", label: "field" },
    { value: "inspection", label: "inspection" },
  ],
};

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  title: z.string().min(1),
  description: z.string().optional().default(""),
  method: z.enum(["bench", "simulation", "field", "inspection"]),
  status: z.enum(["draft", "in_review", "approved", "rejected", "ready", "executed", "failed", "passed", "archived", "obsolete"]),
});

type FormValues = z.infer<typeof schema>;

export function TestCaseForm({
  initial,
  labels: providedLabels,
  profile,
}: {
  initial?: Partial<TestCase>;
  labels?: LabelSet;
  profile?: DomainProfile;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const labels = providedLabels || getLabels("engineering");
  const profileKey = profile ?? "engineering";
  const testMethodOptions = TEST_METHOD_OPTIONS[profileKey];
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      title: initial?.title || "",
      description: initial?.description || "",
      method: initial?.method || "bench",
      status: initial?.status || "draft",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      if (initial?.id) {
        await api.updateTestCase(initial.id, values);
        router.push(`/test-cases/${initial.id}`);
      } else {
        const created = await api.createTestCase(values);
        router.push(`/test-cases/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save test case");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder={`${labels.testCase} key`} {...form.register("key")} />
      </div>
      <Input placeholder={`${labels.testCase} title`} {...form.register("title")} />
      <Textarea placeholder={labels.testCase_description} rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("method")}>
          {testMethodOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        <Select {...form.register("status")}>
          <option value="draft">draft</option>
          <option value="in_review">in_review</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
          <option value="ready">ready</option>
          <option value="executed">executed</option>
          <option value="failed">failed</option>
          <option value="passed">passed</option>
          <option value="archived">archived</option>
          <option value="obsolete">obsolete</option>
        </Select>
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">{`Save ${labels.testCase}`}</Button>
    </form>
  );
}
