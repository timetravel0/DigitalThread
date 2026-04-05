import { Button, Card, CardBody, CardHeader } from "@/components/ui";
import type { LabelSet } from "@/lib/labels";

function lower(value: string) {
  return value.toLowerCase();
}

function stepTone(index: number) {
  if (index === 0) return "accent";
  if (index === 1) return "warning";
  return "success";
}

export function ProjectStartHereCard({
  projectId,
  labels,
}: {
  projectId: string;
  labels: LabelSet;
}) {
  const steps = [
    {
      title: `1. Capture ${lower(labels.requirements)}`,
      description: `Start with the need, goal, or specification that anchors the thread for this project.`,
      href: `/projects/${projectId}/requirements`,
      cta: `Open ${labels.requirements}`,
    },
    {
      title: `2. Connect ${lower(labels.blocks)}`,
      description: `Add the parts or elements that realize each need and make the structure visible.`,
      href: `/projects/${projectId}/blocks`,
      cta: `Open ${labels.blocks}`,
    },
    {
      title: `3. Verify with ${lower(labels.testCases)}`,
      description: `Record checks that prove the requirement is met and keep the verification thread visible.`,
      href: `/projects/${projectId}/tests`,
      cta: `Open ${labels.testCases}`,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="font-semibold">Start here</div>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="text-sm text-muted">
          Choose a simple path first. Add the thing you want to achieve, connect the realization, then attach the checks that prove it works.
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {steps.map((step, index) => (
            <div key={step.title} className="rounded-2xl border border-line bg-panel2 p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="text-sm font-semibold">{step.title}</div>
                <div className={`rounded-full border px-2 py-0.5 text-[0.65rem] uppercase tracking-[0.18em] ${stepTone(index) === "accent" ? "border-accent/40 text-accent" : stepTone(index) === "warning" ? "border-amber-400/40 text-amber-300" : "border-emerald-400/40 text-emerald-300"}`}>
                  Step {index + 1}
                </div>
              </div>
              <div className="mt-2 text-sm text-muted">{step.description}</div>
              <div className="mt-4">
                <Button href={step.href} variant="secondary" className="w-full">
                  {step.cta}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardBody>
    </Card>
  );
}

export function ProjectNavigationGuide({
  projectId,
  labels,
}: {
  projectId: string;
  labels: LabelSet;
}) {
  const groups = [
    {
      title: "Build",
      description: "Create the structure and the objects that realize it.",
      items: [
        { href: `/projects/${projectId}/requirements`, label: labels.requirements },
        { href: `/projects/${projectId}/blocks`, label: labels.blocks },
        { href: `/projects/${projectId}/tests`, label: labels.testCases },
        { href: `/projects/${projectId}/software`, label: "Software" },
      ],
    },
    {
      title: "Trace",
      description: "See how objects connect and where the thread passes through the model.",
      items: [
        { href: `/projects/${projectId}/graph`, label: "Traceability graph" },
        { href: `/projects/${projectId}/matrix`, label: "Matrix view" },
        { href: `/projects/${projectId}/links`, label: labels.links },
      ],
    },
    {
      title: "Govern",
      description: "Review evidence, baselines, and changes without leaving the project.",
      items: [
        { href: `/projects/${projectId}/baselines`, label: labels.baselines },
        { href: `/projects/${projectId}/change-requests`, label: labels.changeRequests },
        { href: `/projects/${projectId}/non-conformities`, label: labels.nonConformities },
        { href: `/projects/${projectId}/review-queue`, label: "Review Queue" },
      ],
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="font-semibold">What to do next</div>
      </CardHeader>
      <CardBody className="space-y-4">
        <div className="text-sm text-muted">
          The navigation below keeps the first step visible and moves deeper tools behind grouped sections.
        </div>
        <div className="space-y-4">
          {groups.map((group) => (
            <div key={group.title} className="rounded-2xl border border-line bg-panel2 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-semibold">{group.title}</div>
                  <div className="mt-1 text-sm text-muted">{group.description}</div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <Button key={item.href} href={item.href} variant="secondary" className="min-w-[10rem]">
                    {item.label}
                  </Button>
                ))}
              </div>
            </div>
          ))}
        </div>
        <details className="rounded-2xl border border-dashed border-line px-4 py-3">
          <summary className="cursor-pointer text-sm font-medium text-text">More tools</summary>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            <Button href={`/projects/${projectId}/validation`} variant="secondary">{labels.requirements} validation</Button>
            <Button href={`/projects/${projectId}/simulation-evidence`} variant="secondary">{labels.simulationEvidence}</Button>
            <Button href={`/projects/${projectId}/operational-evidence`} variant="secondary">{labels.operationalEvidence}</Button>
            <Button href={`/projects/${projectId}/import`} variant="secondary">Import data</Button>
            <Button href={`/projects/${projectId}/sysml`} variant="secondary">SysML</Button>
            <Button href={`/projects/${projectId}/authoritative-sources`} variant="secondary">Authoritative Sources</Button>
          </div>
        </details>
      </CardBody>
    </Card>
  );
}

export function SectionIntroCard({
  title,
  description,
  nextStep,
}: {
  title: string;
  description: string;
  nextStep?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="font-semibold">{title}</div>
      </CardHeader>
      <CardBody className="space-y-2">
        <div className="text-sm text-muted">{description}</div>
        {nextStep ? <div className="text-sm text-text">{nextStep}</div> : null}
      </CardBody>
    </Card>
  );
}
