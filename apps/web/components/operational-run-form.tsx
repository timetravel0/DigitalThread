"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { api } from "@/lib/api-client";
import { Button, Input, Select, Textarea } from "@/components/ui";
import type { OperationalRun } from "@/lib/types";

const schema = z.object({
  project_id: z.string().uuid(),
  key: z.string().min(1),
  date: z.string().min(1),
  drone_serial: z.string().min(1),
  location: z.string().min(1),
  duration_minutes: z.string().min(1),
  max_temperature_c: z.string().optional().default(""),
  battery_consumption_pct: z.string().optional().default(""),
  outcome: z.enum(["success", "degraded", "failure"]),
  notes: z.string().optional().default(""),
  telemetry_json: z.string().optional().default("{}"),
});

type FormValues = z.infer<typeof schema>;

export function OperationalRunForm({ initial }: { initial?: Partial<OperationalRun> }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      project_id: initial?.project_id || "",
      key: initial?.key || "",
      date: initial?.date || "",
      drone_serial: initial?.drone_serial || "",
      location: initial?.location || "",
      duration_minutes: initial?.duration_minutes?.toString() || "",
      max_temperature_c: initial?.max_temperature_c?.toString() || "",
      battery_consumption_pct: initial?.battery_consumption_pct?.toString() || "",
      outcome: initial?.outcome || "success",
      notes: initial?.notes || "",
      telemetry_json: initial?.telemetry_json ? JSON.stringify(initial.telemetry_json, null, 2) : "{}",
    },
  });

  const submit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const parseJson = (raw: string | undefined) => {
        if (!raw?.trim()) return {};
        try {
          return JSON.parse(raw);
        } catch {
          throw new Error("Telemetry JSON must be valid JSON.");
        }
      };
      const payload = {
        project_id: values.project_id,
        key: values.key,
        date: values.date,
        drone_serial: values.drone_serial,
        location: values.location,
        duration_minutes: Number(values.duration_minutes),
        max_temperature_c: values.max_temperature_c ? Number(values.max_temperature_c) : null,
        battery_consumption_pct: values.battery_consumption_pct ? Number(values.battery_consumption_pct) : null,
        outcome: values.outcome,
        notes: values.notes || "",
        telemetry_json: parseJson(values.telemetry_json),
      };
      const created = await api.createOperationalRun(payload);
      router.push(`/operational-runs/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save operational run");
    }
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Input placeholder="Project ID" {...form.register("project_id")} />
        <Input placeholder="Run key" {...form.register("key")} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input type="date" {...form.register("date")} />
        <Input placeholder="Drone serial" {...form.register("drone_serial")} />
      </div>
      <Input placeholder="Location" {...form.register("location")} />
      <div className="grid gap-4 md:grid-cols-2">
        <Input type="number" placeholder="Duration minutes" {...form.register("duration_minutes")} />
        <Select {...form.register("outcome")}>
          <option value="success">success</option>
          <option value="degraded">degraded</option>
          <option value="failure">failure</option>
        </Select>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Input type="number" step="0.1" placeholder="Max temperature C" {...form.register("max_temperature_c")} />
        <Input type="number" step="0.1" placeholder="Battery consumption %" {...form.register("battery_consumption_pct")} />
      </div>
      <Textarea placeholder="Notes" rows={3} {...form.register("notes")} />
      <Textarea placeholder='Telemetry JSON, e.g. {"altitude_m": 43, "return_to_home": true}' rows={6} {...form.register("telemetry_json")} />
      {error ? <div className="text-sm text-danger">{error}</div> : null}
      <Button type="submit">Save operational run</Button>
    </form>
  );
}
