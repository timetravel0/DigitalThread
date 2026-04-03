import { Badge } from "@/components/ui";
import type { AbstractionLevel } from "@/lib/types";

export function ViewCue({ layer }: { layer: AbstractionLevel }) {
  const isPhysical = layer === "physical";

  return (
    <div className={`rounded-2xl border p-4 ${isPhysical ? "border-amber-400/30 bg-amber-500/10" : "border-sky-400/30 bg-sky-500/10"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.2em] text-muted">View cue</div>
          <div className="mt-1 font-semibold">{isPhysical ? "Physical realization" : "Logical architecture"}</div>
        </div>
        <Badge tone={isPhysical ? "warning" : "accent"}>{layer}</Badge>
      </div>
      <p className="mt-3 text-sm text-muted">
        {isPhysical
          ? "This object lives on the realization side of the thread. It represents an implemented part, subsystem, or other physical artifact."
          : "This object lives on the architecture side of the thread. It describes the design intent and structural decomposition before realization."}
      </p>
    </div>
  );
}
