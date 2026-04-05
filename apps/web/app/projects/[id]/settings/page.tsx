import { api } from "@/lib/api-client";
import { Button, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { ProjectSettingsForm } from "@/components/project-settings-form";

export const dynamic = "force-dynamic";

export default async function ProjectSettingsPage({ params }: { params: { id: string } }) {
  const project = await api.project(params.id).catch(() => null);
  if (!project) return <EmptyState title="Project not found" description="The project may have been removed or the API is not available." />;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${project.code} - Settings`}
        description="Adjust project-level context without changing the underlying data."
        action={<Button href={`/projects/${project.id}`}>Back to project</Button>}
      />
      <Card>
        <CardHeader><div className="font-semibold">Domain profile</div></CardHeader>
        <CardBody>
          <ProjectSettingsForm project={project} />
        </CardBody>
      </Card>
    </div>
  );
}
