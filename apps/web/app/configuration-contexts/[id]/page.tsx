import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, SectionTitle, Select } from "@/components/ui";
import {
  ExternalConfigurationItemMappingForm,
  InternalConfigurationItemMappingForm,
} from "@/components/configuration-item-mapping-form";

export const dynamic = "force-dynamic";

export default async function ConfigurationContextPage({ params, searchParams }: { params: { id: string }; searchParams?: { compare_to?: string } }) {
  const data = await api.configurationContext(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Configuration context not found.</div>;

  const projectId = data.context.project_id;
  const isImmutable = data.context.status === "frozen" || data.context.status === "obsolete" || data.context.context_type === "released";
  const [requirements, blocks, tests, artifacts, contexts] = await Promise.all([
    api.requirements(projectId).catch(() => []),
    api.blocks(projectId).catch(() => []),
    api.testCases(projectId).catch(() => []),
    api.externalArtifacts(projectId).catch(() => []),
    api.configurationContexts(projectId).catch(() => []),
  ]);
  const compareTo = searchParams?.compare_to || "";
  const compareTarget = contexts.find((context) => context.id !== data.context.id && context.id === compareTo)?.id || contexts.find((context) => context.id !== data.context.id)?.id || "";
  const comparison = compareTo && compareTo !== data.context.id ? await api.compareConfigurationContexts(data.context.id, compareTo).catch(() => null) : null;

  const internalOptions = [
    ...requirements.map((item) => ({ object_type: "requirement" as const, object_id: item.id, label: `${item.key} - ${item.title}`, version: item.version })),
    ...blocks.map((item) => ({ object_type: "block" as const, object_id: item.id, label: `${item.key} - ${item.name}`, version: item.version })),
    ...tests.map((item) => ({ object_type: "test_case" as const, object_id: item.id, label: `${item.key} - ${item.title}`, version: item.version })),
  ];
  const artifactVersions = artifacts.flatMap((artifact) =>
    (artifact.versions || []).map((version) => ({
      ...version,
      id: version.id,
      label: `${artifact.external_id} - ${artifact.name}`,
    }))
  );

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${data.context.key} - ${data.context.name}`}
        description={data.context.description || "Configuration context"}
        action={
          <div className="flex flex-wrap gap-2">
            {isImmutable ? null : <Button href={`/configuration-contexts/${data.context.id}/edit`} variant="secondary">Edit context</Button>}
            <Button href={`/projects/${projectId}/authoritative-sources?tab=configuration-contexts`} variant="secondary">Back to registry</Button>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-3">
        <Card>
          <CardHeader><div className="font-semibold">Configuration context</div></CardHeader>
          <CardBody className="space-y-3">
            <Row label="Type" value={data.context.context_type} />
            <Row label="Status" value={<Badge tone={data.context.status === "frozen" ? "accent" : data.context.status === "active" ? "success" : "neutral"}>{data.context.status}</Badge>} />
            <Row label="Items" value={data.context.item_count || data.items.length} />
            {isImmutable ? <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100">This context is locked. Frozen, released, or obsolete contexts cannot be edited or remapped.</div> : null}
            <div className="space-y-2 pt-2">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Related baselines</div>
              <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
                Review-gate contexts can point back to the frozen baseline snapshot they align with.
              </div>
              {data.related_baselines.length ? (
                data.related_baselines.map((baseline) => (
                  <Link key={baseline.id} href={`/baselines/${baseline.id}`} className="block rounded-xl border border-line bg-panel2 p-3 hover:border-accent/50">
                    <div className="font-medium">{baseline.name}</div>
                    <div className="text-xs text-muted">{baseline.status}</div>
                  </Link>
                ))
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">No matching baseline found yet.</div>
              )}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Resolved view</div></CardHeader>
          <CardBody className="space-y-4">
            <div className="space-y-3">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Internal</div>
              {data.resolved_view.internal.length ? (
                data.resolved_view.internal.map((item) => (
                  <div key={item.mapping_id} className="rounded-xl border border-line bg-panel2 p-3">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-muted">
                      {item.object_type} v{item.version ?? "?"}
                      {item.role_label ? ` · ${item.role_label}` : ""}
                    </div>
                    {item.notes ? <div className="mt-1 text-xs text-muted">{item.notes}</div> : null}
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted">No internal items.</div>
              )}
            </div>
            <div className="space-y-3">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">External</div>
              {data.resolved_view.external.length ? (
                data.resolved_view.external.map((item) => (
                  <div key={item.mapping_id} className="rounded-xl border border-line bg-panel2 p-3">
                    <div className="font-medium">{item.artifact_name || "External artifact"}</div>
                    <div className="text-xs text-muted">
                      {item.connector_name || "No connector"} · {item.version_label || "version unknown"}
                      {item.revision_label ? ` / ${item.revision_label}` : ""}
                    </div>
                    {item.role_label ? <div className="mt-1 text-xs text-muted">{item.role_label}</div> : null}
                    {item.notes ? <div className="mt-1 text-xs text-muted">{item.notes}</div> : null}
                  </div>
                ))
              ) : (
                <div className="text-sm text-muted">No external items.</div>
              )}
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Compare contexts</div></CardHeader>
          <CardBody className="space-y-4">
            {contexts.filter((context) => context.id !== data.context.id).length ? (
              <form method="get" className="space-y-4">
                <label className="space-y-2 text-sm text-muted">
                  <div className="text-xs uppercase tracking-[0.2em]">Compare to</div>
                  <Select name="compare_to" defaultValue={compareTarget}>
                    <option value="">Select a second context</option>
                    {contexts.filter((context) => context.id !== data.context.id).map((context) => (
                      <option key={context.id} value={context.id}>{context.key} - {context.name}</option>
                    ))}
                  </Select>
                </label>
                <Button type="submit" variant="secondary" className="w-full">Compare</Button>
                <div className="text-sm text-muted">The current context stays visible in the other cards while you inspect differences.</div>
              </form>
            ) : (
              <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
                Create a second configuration context in the same project to compare approved states.
              </div>
            )}
            {comparison ? (
              <div className="space-y-5">
                <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
                  Comparing <span className="text-text">{comparison.left_context.key}</span> against{" "}
                  <span className="text-text">{comparison.right_context.key}</span>.
                </div>
                <div className="grid gap-4 md:grid-cols-3">
                  <Summary label="Added" value={comparison.summary.added} />
                  <Summary label="Removed" value={comparison.summary.removed} />
                  <Summary label="Version changed" value={comparison.summary.version_changed} />
                </div>
                {comparison.groups.length ? (
                  <div className="space-y-4">
                    {comparison.groups.map((group) => (
                      <div key={group.item_kind} className="rounded-2xl border border-line bg-panel2 p-4">
                        <div className="flex items-center justify-between gap-4">
                          <div className="font-semibold">{group.item_kind}</div>
                          <div className="text-xs text-muted">
                            {group.added.length} added · {group.removed.length} removed · {group.version_changed.length} version changed
                          </div>
                        </div>
                        <div className="mt-4 grid gap-4 lg:grid-cols-3">
                          <CompareColumn title="Added" items={group.added} />
                          <CompareColumn title="Removed" items={group.removed} />
                          <CompareColumn title="Version changed" items={group.version_changed} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No differences between the selected contexts.</div>
                )}
              </div>
            ) : compareTo ? (
              <div className="text-sm text-muted">Unable to compare the selected contexts.</div>
            ) : null}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Lifecycle history</div></CardHeader>
        <CardBody className="space-y-3">
          {data.history?.length ? (
            data.history.map((event: any) => (
              <div key={event.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="font-medium">{event.from_status} â†’ {event.to_status}</div>
                  <Badge tone={historyTone(event.to_status)}>{event.action}</Badge>
                </div>
                <div className="mt-1 text-xs text-muted">{event.actor || "system"} Â· {event.created_at}</div>
                {event.comment ? <div className="mt-2 text-sm text-muted">{event.comment}</div> : null}
              </div>
            ))
          ) : (
            <div className="text-sm text-muted">No lifecycle events recorded yet.</div>
          )}
        </CardBody>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader><div className="font-semibold">Add internal item</div></CardHeader>
          <CardBody>
            {isImmutable ? (
              <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
                Internal mappings cannot be changed once a context is frozen, released, or obsolete.
              </div>
            ) : (
              <InternalConfigurationItemMappingForm contextId={data.context.id} internalOptions={internalOptions} />
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader><div className="font-semibold">Add external item</div></CardHeader>
          <CardBody>
            {isImmutable ? (
              <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
                External mappings cannot be changed once a context is frozen, released, or obsolete.
              </div>
            ) : (
              <ExternalConfigurationItemMappingForm contextId={data.context.id} artifactVersions={artifactVersions} />
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader><div className="font-semibold">Configuration items</div></CardHeader>
        <CardBody className="space-y-3">
          {data.items.length ? (
            data.items.map((item: any) => (
              <div key={item.id} className="rounded-xl border border-line bg-panel2 p-3">
                <div className="font-medium">{item.item_kind}</div>
                <div className="text-xs text-muted">
                  {item.internal_object_type || "external"} {item.internal_object_version ? `v${item.internal_object_version}` : ""} {item.role_label ? `· ${item.role_label}` : ""}
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-muted">No mappings yet.</div>
          )}
        </CardBody>
      </Card>

      <Link href={`/projects/${projectId}/authoritative-sources?tab=configuration-contexts`} className="text-sm text-accent">Back to authoritative sources</Link>
    </div>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return <div className="flex items-center justify-between gap-4 rounded-xl border border-line bg-panel2 p-3"><div className="text-sm text-muted">{label}</div><div className="text-sm font-medium">{value}</div></div>;
}

function Summary({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function historyTone(status: string) {
  if (status === "released" || status === "active") return "success";
  if (status === "obsolete" || status === "frozen") return "danger";
  return "neutral";
}

function CompareColumn({ title, items }: { title: string; items: any[] }) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      {items.length ? (
        items.map((item) => (
          <div key={item.key || `${item.label}-${item.object_id || item.external_artifact_version_id}`} className="rounded-xl border border-line bg-panel p-3">
            {item.left || item.right ? (
              <div className="space-y-2">
                <DiffLine label="Before" item={item.left} />
                <DiffLine label="After" item={item.right} />
              </div>
            ) : (
              <>
                <div className="font-medium">{item.label}</div>
                <div className="mt-1 text-xs text-muted">
                  {item.object_type ? `${item.object_type} v${item.object_version ?? "?"}` : null}
                  {item.artifact_name ? `${item.connector_name ? ` · ${item.connector_name}` : ""} · ${item.artifact_name}` : null}
                  {item.version_label ? ` · ${item.version_label}` : ""}
                  {item.revision_label ? ` / ${item.revision_label}` : ""}
                  {item.role_label ? ` · ${item.role_label}` : null}
                </div>
                {item.notes ? <div className="mt-2 text-xs text-muted">{item.notes}</div> : null}
              </>
            )}
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel p-3 text-sm text-muted">None</div>
      )}
    </div>
  );
}

function DiffLine({ label, item }: { label: string; item?: any }) {
  if (!item) return <div className="text-xs text-muted">{label}: none</div>;
  return (
    <div className="rounded-lg border border-line bg-black/10 p-2">
      <div className="text-[11px] uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 text-sm font-medium">{item.label}</div>
      <div className="text-xs text-muted">
        {item.object_type ? `${item.object_type} v${item.object_version ?? "?"}` : null}
        {item.artifact_name ? `${item.connector_name ? ` · ${item.connector_name}` : ""} · ${item.artifact_name}` : null}
        {item.version_label ? ` · ${item.version_label}` : ""}
        {item.revision_label ? ` / ${item.revision_label}` : ""}
        {item.role_label ? ` · ${item.role_label}` : null}
      </div>
      {item.notes ? <div className="mt-2 text-xs text-muted">{item.notes}</div> : null}
    </div>
  );
}
