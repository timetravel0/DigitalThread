import { SectionTitle, Card, CardBody, CardHeader } from "@/components/ui";
import { ProjectForm } from "@/components/project-form";

export default function NewProjectPage() {
  return (
    <div className="space-y-6">
      <SectionTitle
        title="Create project"
        description="Choose a domain profile, then give your project a name and code. You can always change these later."
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
