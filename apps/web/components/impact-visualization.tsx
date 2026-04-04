"use client";

import Link from "next/link";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import { cn } from "@/lib/utils";

export type ImpactVisualizationNode = {
  label: string;
  objectType: string;
  href?: string | null;
  meta?: string | null;
  tone?: "neutral" | "success" | "warning" | "danger" | "accent";
};

export type ImpactVisualizationSection = {
  title: string;
  description?: string;
  items: ImpactVisualizationNode[];
  emptyText?: string;
  tone?: "neutral" | "success" | "warning" | "danger" | "accent";
};

export type ImpactVisualizationRoot = {
  label: string;
  eyebrow?: string;
  description?: string;
  badges?: { label: string; tone?: "neutral" | "success" | "warning" | "danger" | "accent" }[];
};

export function ImpactVisualization({
  title,
  description,
  root,
  sections,
}: {
  title: string;
  description?: string;
  root: ImpactVisualizationRoot;
  sections: ImpactVisualizationSection[];
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-semibold">{title}</div>
            {description ? <div className="mt-1 text-sm text-muted">{description}</div> : null}
          </div>
          {root.badges?.length ? (
            <div className="flex flex-wrap gap-2">
              {root.badges.map((badge) => (
                <Badge key={badge.label} tone={badge.tone ?? "neutral"}>{badge.label}</Badge>
              ))}
            </div>
          ) : null}
        </div>
      </CardHeader>
      <CardBody className="space-y-6">
        <div className="rounded-2xl border border-line bg-panel p-4 shadow-glow">
          <div className="text-xs uppercase tracking-[0.2em] text-muted">{root.eyebrow || "Root object"}</div>
          <div className="mt-2 text-xl font-semibold text-text">{root.label}</div>
          {root.description ? <div className="mt-2 text-sm text-muted">{root.description}</div> : null}
        </div>
        <div className="mx-auto h-8 w-px bg-gradient-to-b from-accent/70 via-line to-transparent" />
        <div className="grid gap-4 xl:grid-cols-2">
          {sections.map((section) => (
            <section key={section.title} className="rounded-2xl border border-line bg-panel2 p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-medium text-text">{section.title}</div>
                  {section.description ? <div className="mt-1 text-xs text-muted">{section.description}</div> : null}
                </div>
                <Badge tone={section.tone ?? "neutral"}>{section.items.length}</Badge>
              </div>
              <div className="mt-4 space-y-2">
                {section.items.length ? (
                  section.items.map((item) => (
                    <ImpactNodeCard key={`${section.title}:${item.objectType}:${item.label}`} item={item} />
                  ))
                ) : (
                  <div className="rounded-xl border border-dashed border-line bg-panel p-3 text-sm text-muted">
                    {section.emptyText || "No items to show."}
                  </div>
                )}
              </div>
            </section>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

function ImpactNodeCard({ item }: { item: ImpactVisualizationNode }) {
  const content = (
    <div className="rounded-xl border border-line bg-panel p-3 transition hover:border-accent/60">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate font-medium text-text">{item.label}</div>
          {item.meta ? <div className="mt-1 text-xs text-muted">{item.meta}</div> : null}
        </div>
        <Badge tone={item.tone ?? "neutral"}>{item.objectType}</Badge>
      </div>
    </div>
  );

  if (!item.href) return content;
  return <Link href={item.href}>{content}</Link>;
}
