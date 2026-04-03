import { api } from "@/lib/api-client";
import { ExternalArtifactForm } from "@/components/external-artifact-form";

export const dynamic = "force-dynamic";

export default async function EditExternalArtifactPage({ params }: { params: { id: string } }) {
  const data = await api.externalArtifact(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">External artifact not found.</div>;
  const connectors = await api.connectors(data.external_artifact.project_id).catch(() => []);
  return <ExternalArtifactForm initial={data.external_artifact} connectors={connectors} />;
}
