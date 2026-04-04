import { api } from "@/lib/api-client";
import { EmptyState, Button } from "@/components/ui";
import { ConfigurationContextForm } from "@/components/configuration-context-form";

export const dynamic = "force-dynamic";

export default async function EditConfigurationContextPage({ params }: { params: { id: string } }) {
  const data = await api.configurationContext(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Configuration context not found.</div>;
  const isImmutable = data.context.status === "frozen" || data.context.status === "obsolete" || data.context.context_type === "released";
  if (isImmutable) {
    return (
      <EmptyState
        title="Context locked"
        description="Frozen, released, or obsolete configuration contexts cannot be edited."
        action={<Button href={`/configuration-contexts/${data.context.id}`} variant="secondary">Back to context</Button>}
      />
    );
  }
  return <ConfigurationContextForm initial={data.context} />;
}
