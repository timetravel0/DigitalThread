"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import { getLabels, type DomainProfile, type LabelSet } from "@/lib/labels";
import { useToast } from "@/lib/toast-context";
import type { TestCase } from "@/lib/types";

type TestMethodValue = "bench" | "simulation" | "field" | "inspection";
type TestCaseStatusValue = "draft" | "in_review" | "approved" | "rejected" | "ready" | "executed" | "failed" | "passed" | "archived" | "obsolete";

type ProjectOption = {
  id: string;
  code: string;
  name: string;
  domain_profile: DomainProfile;
  test_count?: number;
};

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

const STATUS_OPTIONS: Record<DomainProfile, { value: TestCaseStatusValue; label: string }[]> = {
  engineering: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "ready", label: "ready" },
    { value: "executed", label: "executed" },
    { value: "failed", label: "failed" },
    { value: "passed", label: "passed" },
    { value: "archived", label: "archived" },
    { value: "obsolete", label: "obsolete" },
  ],
  manufacturing: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "review" },
    { value: "approved", label: "released" },
    { value: "rejected", label: "rework" },
    { value: "ready", label: "ready" },
    { value: "executed", label: "executed" },
    { value: "failed", label: "failed" },
    { value: "passed", label: "passed" },
    { value: "archived", label: "retired" },
    { value: "obsolete", label: "obsolete" },
  ],
  personal: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "under review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "needs work" },
    { value: "ready", label: "ready" },
    { value: "executed", label: "done" },
    { value: "failed", label: "failed" },
    { value: "passed", label: "passed" },
    { value: "archived", label: "archived" },
    { value: "obsolete", label: "obsolete" },
  ],
  custom: [
    { value: "draft", label: "draft" },
    { value: "in_review", label: "in_review" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "ready", label: "ready" },
    { value: "executed", label: "executed" },
    { value: "failed", label: "failed" },
    { value: "passed", label: "passed" },
    { value: "archived", label: "archived" },
    { value: "obsolete", label: "obsolete" },
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
  projects = [],
  initialProjectId,
}: {
  initial?: Partial<TestCase>;
  labels?: LabelSet;
  profile?: DomainProfile;
  projects?: ProjectOption[];
  initialProjectId?: string;
}) {
  const router = useRouter();
  const { showToast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const labels = providedLabels || getLabels("engineering");
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || initialProjectId || projects[0]?.id || "",
      key: initial?.key || "",
      title: initial?.title || "",
      description: initial?.description || "",
      method: initial?.method || "bench",
      status: initial?.status || "draft",
    },
  });
  const selectedProjectId = useWatch({ control: form.control, name: "project_id" });
  const currentProject = projects.find((project) => project.id === selectedProjectId) || projects[0];
  const resolvedProfile = profile ?? currentProject?.domain_profile ?? "engineering";
  const testMethodOptions = TEST_METHOD_OPTIONS[resolvedProfile];
  const statusOptions = STATUS_OPTIONS[resolvedProfile];

  useEffect(() => {
    if (initial?.id) return;
    if (!currentProject) return;
    if (form.getValues("key")) return;
    const count = currentProject.test_count ?? 0;
    const prefix = currentProject.code.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "").toUpperCase() || "TST";
    form.setValue("key", `${prefix}-TST-${String(count + 1).padStart(3, "0")}`, { shouldDirty: false, shouldTouch: false });
  }, [currentProject, form, initial?.id]);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      if (initial?.id) {
        await api.updateTestCase(initial.id, values);
        router.push(`/test-cases/${initial.id}`);
      } else {
        const created = await api.createTestCase(values);
        showToast({
          message: `${labels.testCases} created`,
          action: {
            label: "View traceability",
            href: `/projects/${values.project_id}/traceability`,
          },
        });
        router.push(`/test-cases/${created.id}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save test case");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("project_id")} disabled={!projects.length}>
          {(projects.length ? projects : currentProject ? [currentProject] : []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.code} - {project.name}
            </option>
          ))}
        </Select>
        <Input placeholder={`${labels.testCase} key`} readOnly {...form.register("key")} />
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
          {statusOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">{`Save ${labels.testCase}`}</Button>
    </form>
  );
}
