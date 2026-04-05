import Link from "next/link";
import { api } from "@/lib/api-client";
import {
  Badge,
  Button,
  Card,
  CardBody,
  CardHeader,
  EmptyState,
  SectionTitle,
  Select,
  StatCard,
} from "@/components/ui";

export const dynamic = "force-dynamic";

export default async function AuthoritativeSourcesPage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams?: { tab?: string; connector_type?: string; artifact_type?: string; compare_left?: string; compare_right?: string };
}) {
  const projectId = params.id;
  const tab = searchParams?.tab || "connectors";
  const [project, summary, connectors, artifacts, links, contexts] = await Promise.all([
    api.project(projectId).catch(() => null),
    api.authoritativeRegistrySummary(projectId).catch(() => null),
    api.connectors(projectId).catch(() => []),
    api.externalArtifacts(projectId, {
      connector_type: searchParams?.connector_type as any,
      artifact_type: searchParams?.artifact_type as any,
    }).catch(() => []),
    api.artifactLinks(projectId).catch(() => []),
    api.configurationContexts(projectId).catch(() => []),
  ]);
  const compareLeft = searchParams?.compare_left || contexts[0]?.id || "";
  const compareRight =
    searchParams?.compare_right || contexts.find((context) => context.id !== compareLeft)?.id || contexts[1]?.id || "";
  const canCompare = tab === "configuration-contexts" && compareLeft && compareRight && compareLeft !== compareRight;
  const comparison = canCompare ? await api.compareConfigurationContexts(compareLeft, compareRight).catch(() => null) : null;

  if (!project) return <EmptyState title="Project not found" description="The project may have been removed or the API is not available." />;

  const externalVersions = artifacts.flatMap((artifact) => artifact.versions || []);

  return (
    <div className="space-y-6">
      <SectionTitle
        title={`${project.code} - Authoritative Sources`}
        description="Federated metadata pointers, configuration contexts, revision snapshot integrity, and the bridge back to baselines. External artifacts are references, not copied source files."
        action={<Button href={`/projects/${project.id}`}>Back to project</Button>}
      />

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Connectors" value={summary?.connectors ?? connectors.length} />
        <StatCard label="External artifacts" value={summary?.external_artifacts ?? artifacts.length} />
        <StatCard label="Artifact versions" value={summary?.external_artifact_versions ?? externalVersions.length} />
        <StatCard label="Artifact links" value={summary?.artifact_links ?? links.length} />
        <StatCard label="Config contexts" value={summary?.configuration_contexts ?? contexts.length} />
        <StatCard label="Mappings" value={summary?.configuration_item_mappings ?? 0} />
      </div>

      <Card>
        <CardHeader>
          <div className="font-semibold">Revision snapshot integrity</div>
        </CardHeader>
        <CardBody className="space-y-4">
          <div className="grid gap-4 md:grid-cols-4">
            <StatCard label="Snapshots" value={summary?.revision_snapshots ?? 0} />
            <StatCard label="Objects checked" value={summary?.revision_snapshot_objects ?? 0} />
            <StatCard label="Broken objects" value={summary?.revision_snapshot_objects_broken ?? 0} />
            <StatCard
              label="Integrity status"
              value={
                <Badge
                  tone={
                    summary?.revision_snapshot_integrity_status === "broken"
                      ? "danger"
                      : summary?.revision_snapshot_integrity_status === "warning"
                        ? "warning"
                        : "success"
                  }
                >
                  {summary?.revision_snapshot_integrity_status || "unknown"}
                </Badge>
              }
            />
          </div>
          {summary?.revision_snapshot_integrity_issues?.length ? (
            <div className="rounded-xl border border-warning/40 bg-warning/10 p-4 text-sm text-text">
              <div className="font-semibold text-warning">Integrity issues detected</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted">
                {summary.revision_snapshot_integrity_issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
              Revision snapshots are chained with content hashes and previous-hash pointers. No integrity issues are currently detected for this project.
            </div>
          )}
        </CardBody>
      </Card>

      <div className="flex flex-wrap gap-2">
        {[
          ["connectors", "Connectors"],
          ["external-artifacts", "External Artifacts"],
          ["artifact-links", "Artifact Links"],
          ["configuration-contexts", "Configuration Contexts"],
        ].map(([value, label]) => (
          <Button key={value} href={`/projects/${project.id}/authoritative-sources?tab=${value}`} variant={tab === value ? "primary" : "secondary"}>
            {label}
          </Button>
        ))}
      </div>

      {tab === "external-artifacts" ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="font-semibold">External artifacts</div>
              <Button href={`/external-artifacts/new?project=${project.id}`}>Create external artifact</Button>
            </div>
          </CardHeader>
          <CardBody className="space-y-4">
            <form method="get" className="grid gap-3 md:grid-cols-3">
              <input type="hidden" name="tab" value="external-artifacts" />
              <Select name="connector_type" defaultValue={searchParams?.connector_type || ""}>
                <option value="">All connector types</option>
                <option value="doors">doors</option>
                <option value="sysml">sysml</option>
                <option value="plm">plm</option>
                <option value="simulation">simulation</option>
                <option value="test">test</option>
                <option value="telemetry">telemetry</option>
                <option value="custom">custom</option>
              </Select>
              <Select name="artifact_type" defaultValue={searchParams?.artifact_type || ""}>
                <option value="">All artifact types</option>
                <option value="requirement">requirement</option>
                <option value="sysml_element">sysml_element</option>
                <option value="block">block</option>
                <option value="cad_part">cad_part</option>
                <option value="software_module">software_module</option>
                <option value="test_case">test_case</option>
                <option value="simulation_model">simulation_model</option>
                <option value="test_result">test_result</option>
                <option value="telemetry_source">telemetry_source</option>
                <option value="document">document</option>
                <option value="other">other</option>
              </Select>
              <Button type="submit">Apply filters</Button>
            </form>
            {artifacts.length ? (
              <div className="space-y-3">
                {artifacts.map((artifact) => (
                  <Link key={artifact.id} href={`/external-artifacts/${artifact.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="font-semibold">{artifact.external_id} - {artifact.name}</div>
                        <div className="mt-1 text-sm text-muted">{artifact.description || "No description"}</div>
                        <div className="mt-2 text-xs text-muted">
                          {artifact.connector_name || "No connector"} · {artifact.connector_type || "connector unknown"} · {artifact.artifact_type}
                        </div>
                      </div>
                      <Badge tone={artifact.status === "active" ? "success" : artifact.status === "deprecated" ? "warning" : "danger"}>{artifact.status}</Badge>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                      <span>Canonical: {artifact.canonical_uri || "none"}</span>
                      <span>Native: {artifact.native_tool_url || "none"}</span>
                      <span>Versions: {(artifact.versions || []).length}</span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No external artifacts yet" description="Register authoritative metadata pointers for external requirements, models, parts, and evidence." action={<Button href={`/external-artifacts/new?project=${project.id}`}>Create external artifact</Button>} />
            )}
          </CardBody>
        </Card>
      ) : tab === "artifact-links" ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="font-semibold">Artifact links</div>
              <Button href={`/projects/${project.id}`}>Use detail pages to add links</Button>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {links.length ? (
              links.map((link) => (
                <div key={link.id} className="rounded-xl border border-line bg-panel2 p-4">
                  <div className="font-semibold">{link.internal_object_label || link.internal_object_type} <span className="text-muted">→</span> {link.external_artifact_name || "External artifact"}</div>
                  <div className="mt-1 text-xs text-muted">
                    {link.relation_type} · {link.connector_name || "No connector"} · {link.external_artifact_version_label || "Unpinned"}
                  </div>
                  {link.rationale ? <div className="mt-2 text-sm text-muted">{link.rationale}</div> : null}
                </div>
              ))
            ) : (
              <EmptyState title="No artifact links yet" description="Link requirements, blocks, and test cases to their authoritative external sources from the relevant detail pages." />
            )}
          </CardBody>
        </Card>
      ) : tab === "configuration-contexts" ? (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="font-semibold">Compare configuration contexts</div>
                <Button href={`/configuration-contexts/new?project=${project.id}`}>Create configuration context</Button>
              </div>
            </CardHeader>
            <CardBody className="space-y-4">
              {contexts.length > 1 ? (
                <form method="get" className="space-y-4">
                  <input type="hidden" name="tab" value="configuration-contexts" />
                  <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
                    <label className="space-y-2 text-sm text-muted">
                      <div className="text-xs uppercase tracking-[0.2em]">Left context</div>
                      <Select name="compare_left" defaultValue={compareLeft}>
                        {contexts.map((context) => (
                          <option key={context.id} value={context.id}>
                            {context.key} - {context.name}
                          </option>
                        ))}
                      </Select>
                    </label>
                    <label className="space-y-2 text-sm text-muted">
                      <div className="text-xs uppercase tracking-[0.2em]">Right context</div>
                      <Select name="compare_right" defaultValue={compareRight}>
                        {contexts.map((context) => (
                          <option key={context.id} value={context.id}>
                            {context.key} - {context.name}
                          </option>
                        ))}
                      </Select>
                    </label>
                    <div className="flex items-end">
                      <Button type="submit" className="w-full md:w-auto">Compare</Button>
                    </div>
                  </div>
                  <div className="text-sm text-muted">
                    Compare two approved snapshots or review gates from the same project. Baselines stay separate from configuration contexts, but both surfaces are linked here for navigation. External version rows show connector, artifact, version, and revision labels when present.
                  </div>
                </form>
              ) : (
                <EmptyState
                  title="Need two contexts"
                  description="Create at least two configuration contexts to compare approved snapshots and mapped versions in the same project."
                  action={<Button href={`/configuration-contexts/new?project=${project.id}`}>Create configuration context</Button>}
                />
              )}
              {comparison ? (
                <div className="space-y-4">
                  <div className="rounded-xl border border-line bg-panel2 p-4 text-sm text-muted">
                    Comparing <span className="text-text">{comparison.left_context.key}</span> against <span className="text-text">{comparison.right_context.key}</span>.
                    Added, removed, and version-changed items are grouped by configuration item type.
                  </div>
                  <div className="grid gap-4 md:grid-cols-3">
                    <StatCard label="Added" value={comparison.summary.added} />
                    <StatCard label="Removed" value={comparison.summary.removed} />
                    <StatCard label="Version changed" value={comparison.summary.version_changed} />
                  </div>
                  {comparison.groups.length ? (
                    comparison.groups.map((group) => (
                      <Card key={group.item_kind}>
                        <CardHeader>
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div className="font-semibold">{group.item_kind}</div>
                            <div className="flex flex-wrap gap-2 text-xs text-muted">
                              <span>{group.added.length} added</span>
                              <span>{group.removed.length} removed</span>
                              <span>{group.version_changed.length} changed</span>
                            </div>
                          </div>
                        </CardHeader>
                        <CardBody className="space-y-4">
                          <ComparisonSection title="Added" items={group.added} emptyMessage="No added items in this type." tone="success" />
                          <ComparisonSection title="Removed" items={group.removed} emptyMessage="No removed items in this type." tone="danger" />
                          <ComparisonVersionSection title="Version changed" items={group.version_changed} emptyMessage="No version changes in this type." />
                        </CardBody>
                      </Card>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">No differences between the selected contexts.</div>
                  )}
                </div>
              ) : searchParams?.compare_left && searchParams?.compare_right && searchParams.compare_left === searchParams.compare_right ? (
                <EmptyState title="Choose two different contexts" description="The compare selection needs distinct left and right contexts from the same project." />
              ) : searchParams?.compare_left && searchParams?.compare_right ? (
                <EmptyState title="Unable to load comparison" description="The selected contexts may be missing or belong to different projects." />
              ) : (
                <div className="rounded-xl border border-dashed border-line bg-panel2 p-4 text-sm text-muted">
                  Pick two configuration contexts and compare them to see which mappings were added, removed, or version-changed.
                </div>
              )}
            </CardBody>
          </Card>
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="font-semibold">Configuration contexts</div>
                <Button href={`/configuration-contexts/new?project=${project.id}`}>Create configuration context</Button>
              </div>
            </CardHeader>
            <CardBody className="space-y-3">
              {contexts.length ? (
                contexts.map((context) => (
                  <Link key={context.id} href={`/configuration-contexts/${context.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="font-semibold">{context.key} - {context.name}</div>
                        <div className="mt-1 text-sm text-muted">{context.description || "No description"}</div>
                        <div className="mt-2 text-xs text-muted">{context.context_type} · {context.item_count || 0} items</div>
                      </div>
                      <Badge tone={context.status === "frozen" ? "accent" : context.status === "active" ? "success" : "neutral"}>{context.status}</Badge>
                    </div>
                  </Link>
                ))
              ) : (
                <EmptyState title="No configuration contexts yet" description="Create a configuration context to snapshot internal versions and external authoritative references together." action={<Button href={`/configuration-contexts/new?project=${project.id}`}>Create configuration context</Button>} />
              )}
            </CardBody>
          </Card>
        </div>
      ) : (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="font-semibold">Connectors</div>
              <Button href={`/connectors/new?project=${project.id}`}>Create connector</Button>
            </div>
          </CardHeader>
          <CardBody className="space-y-3">
            {connectors.length ? (
              connectors.map((connector) => (
                <Link key={connector.id} href={`/connectors/${connector.id}`} className="block rounded-xl border border-line bg-panel2 p-4 hover:border-accent/50">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="font-semibold">{connector.name}</div>
                      <div className="mt-1 text-sm text-muted">{connector.description || "No description"}</div>
                      <div className="mt-2 text-xs text-muted">{connector.connector_type} · {connector.base_url || "No base URL"} · {connector.artifact_count || 0} artifacts</div>
                    </div>
                    <Badge tone={connector.is_active ? "success" : "neutral"}>{connector.is_active ? "active" : "inactive"}</Badge>
                  </div>
                </Link>
              ))
            ) : (
              <EmptyState title="No connectors yet" description="Register the authoritative external tools that own requirements, models, parts, or evidence." action={<Button href={`/connectors/new?project=${project.id}`}>Create connector</Button>} />
            )}
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function ComparisonSection({
  title,
  items,
  emptyMessage,
  tone,
}: {
  title: string;
  items: { label: string; object_type?: string | null; object_id?: string | null; object_version?: number | null; version_label?: string | null; revision_label?: string | null; connector_name?: string | null; artifact_name?: string | null; artifact_type?: string | null; role_label?: string | null; notes?: string | null }[];
  emptyMessage: string;
  tone: "success" | "danger";
}) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      {items.length ? (
        items.map((item) => (
          <div key={`${title}-${item.label}-${item.object_id || item.version_label || item.object_version || "item"}`} className={`rounded-xl border p-3 text-sm ${tone === "success" ? "border-success/30 bg-success/10" : "border-danger/30 bg-danger/10"}`}>
            <div className="font-medium text-text">{item.label}</div>
            <div className="mt-1 text-xs text-muted">
              {item.object_type || item.artifact_type || "item"}
              {item.object_version ? ` v${item.object_version}` : ""}
              {item.version_label ? ` · ${item.version_label}` : ""}
              {item.revision_label ? ` / ${item.revision_label}` : ""}
              {item.connector_name ? ` · ${item.connector_name}` : ""}
            </div>
            {item.role_label ? <div className="mt-2 text-xs text-muted">{item.role_label}</div> : null}
            {item.notes ? <div className="mt-1 text-xs text-muted">{item.notes}</div> : null}
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">{emptyMessage}</div>
      )}
    </div>
  );
}

function ComparisonVersionSection({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: { key: string; left?: { label: string; object_type?: string | null; object_id?: string | null; object_version?: number | null; version_label?: string | null; revision_label?: string | null; connector_name?: string | null; artifact_name?: string | null; artifact_type?: string | null; role_label?: string | null; notes?: string | null } | null; right?: { label: string; object_type?: string | null; object_id?: string | null; object_version?: number | null; version_label?: string | null; revision_label?: string | null; connector_name?: string | null; artifact_name?: string | null; artifact_type?: string | null; role_label?: string | null; notes?: string | null } | null }[];
  emptyMessage: string;
}) {
  return (
    <div className="space-y-2">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{title}</div>
      {items.length ? (
        items.map((item) => (
          <div key={`${title}-${item.key}`} className="grid gap-3 md:grid-cols-2">
            <ComparisonSideCard label="Left" item={item.left} />
            <ComparisonSideCard label="Right" item={item.right} />
          </div>
        ))
      ) : (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">{emptyMessage}</div>
      )}
    </div>
  );
}

function ComparisonSideCard({
  label,
  item,
}: {
  label: string;
  item?: { label: string; object_type?: string | null; object_id?: string | null; object_version?: number | null; version_label?: string | null; revision_label?: string | null; connector_name?: string | null; artifact_name?: string | null; artifact_type?: string | null; role_label?: string | null; notes?: string | null } | null;
}) {
  if (!item) {
    return <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-sm text-muted">{label} item missing</div>;
  }
  return (
    <div className="rounded-xl border border-accent/20 bg-slate-950/30 p-3 text-sm">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-1 font-medium text-text">{item.label}</div>
      <div className="mt-1 text-xs text-muted">
        {item.object_type || item.artifact_type || "item"}
        {item.object_version ? ` v${item.object_version}` : ""}
        {item.version_label ? ` · ${item.version_label}` : ""}
        {item.revision_label ? ` / ${item.revision_label}` : ""}
        {item.connector_name ? ` · ${item.connector_name}` : ""}
      </div>
      {item.role_label ? <div className="mt-2 text-xs text-muted">{item.role_label}</div> : null}
      {item.notes ? <div className="mt-1 text-xs text-muted">{item.notes}</div> : null}
    </div>
  );
}
