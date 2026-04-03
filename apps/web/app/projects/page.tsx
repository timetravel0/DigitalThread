import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import type { Project } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ProjectsPage() {
  let projects: Project[] = [];
  try {
    projects = await api.projects();
  } catch {
    projects = [];
  }

  return (
    <div className="space-y-6">
      <SectionTitle title="Projects" description="Project portfolio and entry point to the digital thread." />
      <Card>
        <CardHeader>
          <div className="font-semibold">Project list</div>
        </CardHeader>
        <CardBody>
          {projects.length ? (
            <div className="space-y-3">
              {projects.map((project) => (
                <Link key={project.id} href={`/projects/${project.id}`} className="block rounded-2xl border border-line bg-panel2 p-4 hover:border-accent/50">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="font-semibold">{project.code} - {project.name}</div>
                      <div className="mt-1 text-sm text-muted">{project.description}</div>
                    </div>
                    <Badge tone={project.status === "active" ? "success" : "neutral"}>{project.status}</Badge>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState title="No projects yet" description="Seed the demo project to start exploring ThreadLite." action={<Button href="/dashboard">Go to dashboard</Button>} />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

