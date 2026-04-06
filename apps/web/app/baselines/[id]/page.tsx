import Link from "next/link";
import { api } from "@/lib/api-client";
import { Badge, Button, Card, CardBody, CardHeader, EmptyState, SectionTitle, Select } from "@/components/ui";
import { BaselineActions } from "@/components/baseline-actions";

export const dynamic = "force-dynamic";

export default async function BaselinePage({ params, searchParams }: { params: { id: string }; searchParams?: { compare_to?: string; compare_baseline_to?: string } }) {
  const data = await api.baseline(params.id).catch(() => null);
  if (!data) return <div className="text-sm text-muted">Baseline not found.</div>;
  const projectId = data.baseline.project_id;
  const [contexts, baselines] = await Promise.all([
    api.configurationContexts(projectId).catch(() => []),
    api.baselines(projectId).catch(() => []),
  ]);
  const compareTo = searchParams?.compare_to || "";
  const comparison = compareTo ? await api.compareBaselineToConfigurationContext(data.baseline.id, compareTo).catch(() => null) : null;
  const compareBaselineTo = searchParams?.compare_baseline_to || "";
  const baselineComparison = compareBaselineTo ? await api.compareBaselines(data.baseline.id, compareBaselineTo).catch(() => null) : null;
  return (
    <div className="space-y-6">
      <SectionTitle
        title={data.baseline.name}
        description={data.baseline.description || "Frozen internal snapshot"}
        action={
          <div className="flex flex-wrap gap-2">
            <Button href={`/projects/${projectId}/baselines`} variant="secondary">Back to baselines</Button>
            <Button href={`/projects/${projectId}/authoritative-sources?tab=configuration-contexts`} variant="secondary">Open configuration contexts</Button>
          </div>
        }
      />
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="font-semibold">Baseline bridge context</div>
            <span className="text-xs uppercase tracking-[0.2em] text-muted">Read-only projection</span>
          </div>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
            This baseline is surfaced as a frozen configuration-context projection so review gates can compare approved snapshots without changing the baseline model.
          </div>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <Stat label="Bridge key" value={data.bridge_context.key} />
            <Stat label="Bridge name" value={data.bridge_context.name} />
            <Stat label="Bridge status" value={<Badge tone="accent">{data.bridge_context.status}</Badge>} />
            <Stat label="Items" value={data.bridge_context.item_count} />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <Stat
              label="Release flag"
              value={<Badge tone={data.baseline.release_flag ? "danger" : "neutral"}>{data.baseline.release_flag ? "Released" : "Not released"}</Badge>}
            />
            <Stat label="Baseline status" value={<Badge tone={data.baseline.status === "released" ? "success" : "neutral"}>{data.baseline.status}</Badge>} />
          </div>
          <div className="rounded-xl border border-dashed border-line bg-panel p-3">
            <div className="mb-3 text-sm font-medium">Baseline lifecycle actions</div>
            <BaselineActions id={data.baseline.id} status={data.baseline.status} />
          </div>
          <div className="rounded-xl border border-dashed border-line bg-panel p-3 text-sm text-muted">
            Bridge source: <span className="text-text">{data.bridge_context.baseline_name}</span>
          </div>
          {data.related_configuration_contexts.length ? (
            <div className="space-y-2">
              <div className="text-xs uppercase tracking-[0.2em] text-muted">Realized by</div>
              <div className="flex flex-wrap gap-2">
                {data.related_configuration_contexts.map((context: any) => (
                  <Link key={context.id} href={`/configuration-contexts/${context.id}`} className="rounded-full border border-line bg-panel px-3 py-1 text-sm text-muted hover:border-accent/50 hover:text-text">
                    {context.key}
                  </Link>
                ))}
              </div>
            </div>
          ) : null}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Lifecycle history</div></CardHeader>
        <CardBody className="space-y-3">
          {data.history.length ? (
            data.history.map((event) => (
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
            <EmptyState
              title="No lifecycle events yet"
              description="A baseline becomes meaningful when it has a clear release or obsolescence history. Record the lifecycle action so reviewers can see how this snapshot is being used."
            />
          )}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Baseline items</div></CardHeader>
        <CardBody className="space-y-3">
          <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
            Baselines are frozen internal snapshots. They capture approved object versions without the broader external version mappings used by configuration contexts.
          </div>
          {data.items.map((item: any) => (
            <div key={item.id} className="rounded-xl border border-line bg-panel2 p-3">
              <div className="font-medium">{item.object_type} - {item.object_id}</div>
              <div className="text-xs text-muted">Version {item.object_version}</div>
            </div>
          ))}
        </CardBody>
      </Card>
      <Card>
        <CardHeader><div className="font-semibold">Related configuration contexts</div></CardHeader>
        <CardBody className="space-y-3">
          <div className="rounded-xl border border-line bg-panel2 p-3 text-sm text-muted">
            These configuration contexts realize the same approved internal item set as the baseline bridge.
          </div>
          {data.related_configuration_contexts.length ? (
            data.related_configuration_contexts.map((context: any) => (
              <Link key={context.id} href={`/configuration-contexts/${context.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold">{context.key} - {context.name}</div>
                    <div className="mt-1 text-sm text-muted">{context.context_type}</div>
                  </div>
                  <Badge tone={context.status === "frozen" ? "accent" : context.status === "active" ? "success" : "neutral"}>{context.status}</Badge>
                </div>
              </Link>
            ))
          ) : (
            <EmptyState
              title="No matching configuration context"
              description="A matching configuration context appears when another snapshot contains the same approved item set as this baseline. Create or update a context in the authoritative sources area to make the comparison possible."
              action={<Button href={`/projects/${projectId}/authoritative-sources?tab=configuration-contexts`} variant="secondary">Open authoritative sources</Button>}
            />
          )}
        </CardBody>
      </Card>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="font-semibold">Compare baseline to context</div>
            <span className="text-xs uppercase tracking-[0.2em] text-muted">Read-only comparison</span>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          {contexts.length ? (
            <form method="get" className="space-y-4">
              <label className="space-y-2 text-sm text-muted">
                <div className="text-xs uppercase tracking-[0.2em]">Context</div>
                <Select name="compare_to" defaultValue={compareTo}>
                  <option value="">Select a configuration context</option>
                  {contexts.map((context) => (
                    <option key={context.id} value={context.id}>
                      {context.key} - {context.name}
                    </option>
                  ))}
                </Select>
              </label>
              <Button type="submit" variant="secondary">Compare</Button>
              <div className="text-sm text-muted">
                Compare the frozen baseline snapshot with a review gate or working context to inspect added, removed, and version-changed items.
              </div>
            </form>
          ) : (
            <EmptyState
              title="No configuration contexts yet"
              description="Configuration contexts belong here when you want to compare a working or review-gate snapshot against a baseline. Add one in authoritative sources so the approved item set can be compared later."
              action={<Button href={`/configuration-contexts/new?project=${projectId}`}>Create configuration context</Button>}
            />
          )}
          {comparison ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
                Comparing <span className="text-text">{comparison.baseline.name}</span> against{" "}
                <span className="text-text">{comparison.configuration_context.key}</span>.
                Added, removed, and version-changed items are grouped by item kind.
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
                      <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="font-semibold">{group.item_kind}</div>
                        <div className="text-xs text-muted">
                          {group.added.length} added · {group.removed.length} removed · {group.version_changed.length} version changed
                        </div>
                      </div>
                      <div className="mt-4 grid gap-4 lg:grid-cols-3">
                        <ComparisonColumn title="Added" items={group.added} />
                        <ComparisonColumn title="Removed" items={group.removed} />
                        <ComparisonVersionColumn title="Version changed" items={group.version_changed} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No differences between the selected baseline and context.</div>
              )}
            </div>
          ) : compareTo ? (
            <div className="text-sm text-muted">Unable to compare the selected baseline and context.</div>
          ) : null}
        </CardBody>
      </Card>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="font-semibold">Compare baseline to baseline</div>
            <span className="text-xs uppercase tracking-[0.2em] text-muted">Approved snapshot comparison</span>
          </div>
        </CardHeader>
        <CardBody className="space-y-4">
          {baselines.filter((baseline) => baseline.id !== data.baseline.id).length ? (
            <form method="get" className="space-y-4">
              <label className="space-y-2 text-sm text-muted">
                <div className="text-xs uppercase tracking-[0.2em]">Baseline</div>
                <Select name="compare_baseline_to" defaultValue={compareBaselineTo}>
                  <option value="">Select a second baseline</option>
                  {baselines.filter((baseline) => baseline.id !== data.baseline.id).map((baseline) => (
                    <option key={baseline.id} value={baseline.id}>
                      {baseline.name}
                    </option>
                  ))}
                </Select>
              </label>
              <Button type="submit" variant="secondary">Compare</Button>
              <div className="text-sm text-muted">
                Compare two frozen baseline snapshots to inspect added, removed, and version-changed items by type.
              </div>
            </form>
          ) : (
            <EmptyState
              title="No second baseline yet"
              description="A second baseline belongs here when you need to compare two approved snapshots directly. Create or release another baseline in the project once the thread has changed enough to justify a comparison."
            />
          )}
          {baselineComparison ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
                Comparing <span className="text-text">{baselineComparison.left_baseline.name}</span> against{" "}
                <span className="text-text">{baselineComparison.right_baseline.name}</span>.
                Added, removed, and version-changed items are grouped by item kind.
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                <Summary label="Added" value={baselineComparison.summary.added} />
                <Summary label="Removed" value={baselineComparison.summary.removed} />
                <Summary label="Version changed" value={baselineComparison.summary.version_changed} />
              </div>
              {baselineComparison.groups.length ? (
                <div className="space-y-4">
                  {baselineComparison.groups.map((group) => (
                    <div key={group.item_kind} className="rounded-2xl border border-line bg-panel2 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-4">
                        <div className="font-semibold">{group.item_kind}</div>
                        <div className="text-xs text-muted">
                          {group.added.length} added Â· {group.removed.length} removed Â· {group.version_changed.length} version changed
                        </div>
                      </div>
                      <div className="mt-4 grid gap-4 lg:grid-cols-3">
                        <ComparisonColumn title="Added" items={group.added} />
                        <ComparisonColumn title="Removed" items={group.removed} />
                        <ComparisonVersionColumn title="Version changed" items={group.version_changed} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No differences between the selected baselines.</div>
              )}
            </div>
          ) : compareBaselineTo ? (
            <div className="text-sm text-muted">Unable to compare the selected baselines.</div>
          ) : null}
        </CardBody>
      </Card>
      <Link href={`/projects/${projectId}`} className="text-sm text-accent">Back to project workspace</Link>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded-xl border border-line bg-panel2 p-3">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-sm font-medium">{value}</div>
    </div>
  );
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
  if (status === "released") return "success";
  if (status === "obsolete") return "danger";
  return "neutral";
}

function ComparisonColumn({ title, items }: { title: string; items: any[] }) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      {items.length ? (
        items.map((item) => (
          <div key={item.key || `${item.label}-${item.object_id || item.external_artifact_version_id}`} className="rounded-xl border border-line bg-panel p-3">
            <div className="font-medium">{item.label}</div>
            <div className="mt-1 text-xs text-muted">
              {item.object_type ? `${item.object_type} v${item.object_version ?? "?"}` : null}
              {item.artifact_name ? `${item.connector_name ? ` · ${item.connector_name}` : ""} · ${item.artifact_name}` : null}
              {item.version_label ? ` · ${item.version_label}` : ""}
              {item.revision_label ? ` / ${item.revision_label}` : ""}
              {item.role_label ? ` · ${item.role_label}` : null}
            </div>
            {item.notes ? <div className="mt-2 text-xs text-muted">{item.notes}</div> : null}
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel p-3 text-sm text-muted">None</div>
      )}
    </div>
  );
}

function ComparisonVersionColumn({ title, items }: { title: string; items: any[] }) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      {items.length ? (
        items.map((item) => (
          <div key={item.key} className="rounded-xl border border-line bg-panel p-3">
            <div className="space-y-2">
              <ComparisonEntry label="Before" item={item.left} />
              <ComparisonEntry label="After" item={item.right} />
            </div>
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel p-3 text-sm text-muted">None</div>
      )}
    </div>
  );
}

function ComparisonEntry({ label, item }: { label: string; item?: any }) {
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
