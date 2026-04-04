import Link from "next/link";
import type { ReactNode } from "react";
import { api } from "@/lib/api-client";
import { Badge, Card, CardBody, CardHeader, EmptyState, SectionTitle } from "@/components/ui";
import { SimulationEvidenceCard } from "@/components/simulation-evidence-card";

export const dynamic = "force-dynamic";

export default async function FMIContractPage({ params }: { params: { id: string } }) {
  const detail = await api.fmiContractDetail(params.id).catch(() => null);
  if (!detail) return <div className="text-sm text-muted">FMI contract not found.</div>;

  const contract = detail.fmi_contract;

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${contract.key} - ${contract.name}`}
        description="An FMI-style placeholder contract that gives simulation evidence a clear model reference structure."
        action={<Link href={`/projects/${contract.project_id}/fmi`} className="rounded-full border border-line px-3 py-1.5 text-sm text-text hover:bg-white/5">Back to project contracts</Link>}
      />
      <Card>
        <CardHeader><div className="font-semibold">Contract record</div></CardHeader>
        <CardBody className="space-y-3">
          <Row label="Model identifier" value={contract.model_identifier} />
          <Row label="Model version" value={contract.model_version || "Not provided"} />
          <Row label="Model URI" value={contract.model_uri || "Not provided"} />
          <Row label="Adapter profile" value={contract.adapter_profile || "Not provided"} />
          <Row label="Contract version" value={contract.contract_version} />
          <Row label="Linked simulation evidence" value={<Badge tone="accent">{contract.linked_simulation_evidence_count}</Badge>} />
          {Object.keys(contract.metadata_json || {}).length ? (
            <div className="rounded-xl border border-line bg-panel2 p-3">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Metadata</div>
              <pre className="mt-2 whitespace-pre-wrap text-xs text-muted">{JSON.stringify(contract.metadata_json, null, 2)}</pre>
            </div>
          ) : null}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Linked simulation evidence</div></CardHeader>
        <CardBody className="space-y-4">
          {detail.simulation_evidence.length ? (
            detail.simulation_evidence.map((evidence) => (
              <SimulationEvidenceCard key={evidence.id} evidence={evidence} objectHref={objectHref} />
            ))
          ) : (
            <EmptyState title="No simulation evidence linked yet" description="Create or edit simulation evidence to reference this contract." />
          )}
        </CardBody>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3">
      <div className="text-sm text-muted">{label}</div>
      <div className="text-sm font-medium">{value}</div>
    </div>
  );
}

function objectHref(objectType: string, objectId: string) {
  if (objectType === "requirement") return `/requirements/${objectId}`;
  if (objectType === "test_case") return `/test-cases/${objectId}`;
  if (objectType === "verification_evidence") return `/verification-evidence/${objectId}`;
  if (objectType === "simulation_evidence") return `/simulation-evidence/${objectId}`;
  if (objectType === "fmi_contract") return `/fmi-contracts/${objectId}`;
  return null;
}
