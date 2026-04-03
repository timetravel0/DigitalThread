export function SimulationEvidenceMetadata({ metadataJson }: { metadataJson?: Record<string, unknown> | null }) {
  if (!metadataJson || typeof metadataJson !== "object") return null;
  const simulation = (metadataJson.simulation as Record<string, unknown> | undefined) || metadataJson;
  if (!simulation || typeof simulation !== "object") return null;

  const model = typeof simulation.model === "string" ? simulation.model : null;
  const scenario = typeof simulation.scenario === "string" ? simulation.scenario : null;
  const inputs = simulation.inputs ?? null;
  const outputs = simulation.outputs ?? null;

  if (!model && !scenario && inputs == null && outputs == null) return null;

  return (
    <div className="mt-3 space-y-3 rounded-xl border border-dashed border-line bg-slate-950/30 p-3 text-xs text-muted">
      <div className="font-medium text-text">Simulation details</div>
      {model ? <DetailRow label="Model" value={model} /> : null}
      {scenario ? <DetailRow label="Scenario" value={scenario} /> : null}
      {inputs ? <JsonBlock label="Inputs" value={inputs} /> : null}
      {outputs ? <JsonBlock label="Outputs" value={outputs} /> : null}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="font-medium text-text">{label}:</span> <span>{value}</span>
    </div>
  );
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <div className="font-medium text-text">{label}:</div>
      <pre className="mt-1 overflow-x-auto rounded-lg border border-white/10 bg-black/20 p-2 text-[11px] text-muted">
        {JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}
