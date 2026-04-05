import { api } from "@/lib/api-client";
import { EmptyState, SectionTitle } from "@/components/ui";
import { ComponentForm } from "@/components/component-form";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function NewComponentPage({ searchParams }: { searchParams: { project?: string } }) {
  const projects = await api.projects().catch(() => []);
  if (!projects.length) {
    return (
      <div className="space-y-6">
        <SectionTitle
          title="Create component"
          description="Pick a project and define a realization object."
        />
        <EmptyState
          title="No projects available"
          description="Create a project first, then add components to it."
          action={<Link href="/projects/new" className="text-sm font-medium text-accent">Create project</Link>}
        />
      </div>
    );
  }
  const projectsWithCounts = await Promise.all(
    projects.map(async (project) => ({
      id: project.id,
      code: project.code,
      name: project.name,
      domain_profile: project.domain_profile,
      component_count: (await api.components(project.id).catch(() => [])).length,
    }))
  );
  const initialProjectId = searchParams.project && projectsWithCounts.some((project) => project.id === searchParams.project)
    ? searchParams.project
    : projectsWithCounts[0].id;

  return (
    <div className="space-y-6">
      <SectionTitle
        title="Create component"
        description="Choose a project, let the element key auto-fill, and define the realization object."
      />
      <ComponentForm projects={projectsWithCounts} initialProjectId={initialProjectId} />
    </div>
  );
}
