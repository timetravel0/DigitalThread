import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import type { VerificationStatusBreakdown } from "@/lib/types";

const statusMeta: Array<{
  key: keyof VerificationStatusBreakdown;
  label: string;
  tone: "success" | "warning" | "danger" | "neutral" | "accent";
}> = [
  { key: "verified", label: "Verified", tone: "success" },
  { key: "partially_verified", label: "Partially verified", tone: "warning" },
  { key: "at_risk", label: "At risk", tone: "warning" },
  { key: "failed", label: "Failed", tone: "danger" },
  { key: "not_covered", label: "Not covered", tone: "neutral" },
];

export function VerificationStatusBreakdownCard({
  breakdown,
  title = "Verification status distribution",
}: {
  breakdown: VerificationStatusBreakdown;
  title?: string;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="font-semibold">{title}</div>
        <div className="mt-1 text-xs text-muted">Computed from linked verification evidence and compatibility fallback where needed.</div>
      </CardHeader>
      <CardBody className="space-y-2">
        {statusMeta.map((item) => (
          <div key={item.key} className="flex items-center justify-between gap-3 rounded-xl border border-line bg-panel2 px-3 py-2">
            <div className="flex items-center gap-2">
              <Badge tone={item.tone}>{item.label}</Badge>
            </div>
            <div className="text-sm font-medium">{breakdown[item.key]}</div>
          </div>
        ))}
      </CardBody>
    </Card>
  );
}
