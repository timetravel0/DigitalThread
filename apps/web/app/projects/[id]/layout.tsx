import { api } from "@/lib/api-client";
import { ProjectProvider } from "@/lib/projectContext";

export default async function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { id: string };
}) {
  const project = await api.project(params.id).catch(() => null);
  if (!project) return children;
  return (
    <ProjectProvider projectId={project.id} profile={project.domain_profile}>
      {children}
    </ProjectProvider>
  );
}
