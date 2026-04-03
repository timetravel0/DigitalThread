import { SectionTitle, Card, CardBody, CardHeader } from "@/components/ui";
import { ProjectForm } from "@/components/project-form";

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <SectionTitle
        title="Create project"
        description="Start a new engineering thread from scratch. The project is blank; you add requirements, blocks, tests, and traceability next."
      />
      <Card>
        <CardHeader><div className="font-semibold">Project details</div></CardHeader>
        <CardBody>
          <ProjectForm />
        </CardBody>
      </Card>
    </div>
  );
}
