"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import { ProjectProfileSelector } from "@/components/project-profile-selector";
import { getLabels, type DomainProfile } from "@/lib/labels";

const schema = z.object({
  code: z.string().min(1, "Project code is required"),
  name: z.string().min(1, "Project name is required"),
  description: z.string().optional().default(""),
  domain_profile: z.enum(["engineering", "manufacturing", "personal"]),
  status: z.enum(["draft", "active", "archived"]),
});

type FormValues = z.infer<typeof schema>;

export function ProjectForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      code: "",
      name: "",
      description: "",
      domain_profile: "engineering",
      status: "draft",
    },
  });
  const profile = form.watch("domain_profile") as DomainProfile;
  const labels = getLabels(profile);

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const created = await api.createProject(values);
      router.push(`/projects/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create project");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <ProjectProfileSelector
        value={form.watch("domain_profile") as DomainProfile}
        onChange={(next) => form.setValue("domain_profile", next as "engineering" | "manufacturing" | "personal", { shouldDirty: true, shouldValidate: true })}
      />
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project code" {...form.register("code")} />
        <Input placeholder="Project name" {...form.register("name")} />
      </div>
      <Textarea placeholder={`Project description - ${labels.requirement_description}`} rows={4} {...form.register("description")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Select {...form.register("status")}>
          <option value="draft">draft</option>
          <option value="active">active</option>
          <option value="archived">archived</option>
        </Select>
      </div>
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Create project</Button>
    </form>
  );
}
