import Link from "next/link";
import { Badge, Card, CardBody, EmptyState } from "@/components/ui";
import type {
  ArtifactLink,
  Block,
  BlockTreeNode,
  Component,
  ExternalArtifact,
  Link as TraceLink,
  OperationalRun,
  Requirement,
  SysMLRelation,
  TestCase,
  VerificationEvidence,
} from "@/lib/types";

type GraphFocus = "core" | "all" | "requirements" | "blocks" | "parts" | "tests" | "evidence";
type GraphKind = "requirement" | "block" | "component" | "external_artifact" | "test_case" | "operational_run" | "verification_evidence";
type GraphTone = "accent" | "success" | "warning" | "neutral" | "danger";

interface GraphNode {
  id: string;
  kind: GraphKind;
  label: string;
  href?: string;
  subtitle?: string;
  status?: string | null;
  detail?: string | null;
  lane: number;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
  tone: GraphTone;
}

interface TraceabilityGraphProps {
  focus: GraphFocus;
  selectedNodeId?: string | null;
  selectionBaseHref: string;
  blocks: Block[];
  tree: BlockTreeNode[];
  requirements: Requirement[];
  components: Component[];
  externalArtifacts: ExternalArtifact[];
  tests: TestCase[];
  runs: OperationalRun[];
  links: TraceLink[];
  artifactLinks: ArtifactLink[];
  sysmlRelations: SysMLRelation[];
  evidence: VerificationEvidence[];
}

const laneOrder: GraphKind[] = ["requirement", "block", "component", "external_artifact", "test_case", "operational_run", "verification_evidence"];

const focusKinds: Record<GraphFocus, GraphKind[]> = {
  core: ["requirement", "block", "component", "external_artifact", "test_case"],
  all: laneOrder,
  requirements: ["requirement", "component", "external_artifact", "test_case"],
  blocks: ["block", "component", "external_artifact"],
  parts: ["component", "external_artifact"],
  tests: ["test_case", "component", "external_artifact"],
  evidence: ["operational_run", "verification_evidence"],
};

const focusRelations: Record<GraphFocus, string[]> = {
  core: ["contains", "contain", "satisfy", "satisfies", "verify", "verifies", "deriveReqt", "trace", "allocated_to", "maps_to", "authoritative_reference", "validated_against", "synchronized_with", "derived_from_external", "uses", "refine"],
  all: [],
  requirements: ["deriveReqt", "satisfy", "satisfies", "verify", "verifies", "trace", "allocated_to", "maps_to", "authoritative_reference", "validated_against", "derived_from_external", "synchronized_with", "uses"],
  blocks: ["contains", "contain", "satisfy", "satisfies", "verify", "verifies", "deriveReqt", "trace", "allocated_to", "maps_to", "authoritative_reference", "validated_against", "derived_from_external", "synchronized_with", "uses"],
  parts: ["allocate", "allocated_to", "refine", "trace", "maps_to", "authoritative_reference", "validated_against", "derived_from_external", "synchronized_with"],
  tests: ["verify", "verifies", "satisfy", "satisfies", "trace", "validated_against", "derived_from_external"],
  evidence: ["reports_on", "evidence_of"],
};

const kindMeta: Record<GraphKind, { label: string; tone: GraphTone; border: string; fill: string }> = {
  requirement: { label: "Requirement", tone: "accent", border: "border-sky-400/40", fill: "bg-sky-500/10" },
  block: { label: "Block", tone: "neutral", border: "border-cyan-400/40", fill: "bg-cyan-500/10" },
  component: { label: "Part", tone: "warning", border: "border-amber-400/40", fill: "bg-amber-500/10" },
  external_artifact: { label: "CAD part", tone: "warning", border: "border-orange-400/40", fill: "bg-orange-500/10" },
  test_case: { label: "Test", tone: "success", border: "border-emerald-400/40", fill: "bg-emerald-500/10" },
  operational_run: { label: "Operational evidence", tone: "neutral", border: "border-slate-400/40", fill: "bg-slate-500/10" },
  verification_evidence: { label: "Evidence", tone: "warning", border: "border-orange-400/40", fill: "bg-orange-500/10" },
};

const relationTone: Record<string, GraphTone> = {
  contains: "neutral",
  satisfy: "accent",
  verify: "success",
  deriveReqt: "warning",
  trace: "accent",
  allocate: "accent",
  refine: "accent",
  allocated_to: "warning",
  maps_to: "accent",
  authoritative_reference: "neutral",
  validated_against: "success",
  synchronized_with: "accent",
  derived_from_external: "warning",
  verifies: "success",
  reports_on: "neutral",
  evidence_of: "warning",
};

export function TraceabilityGraph({
  focus,
  selectedNodeId,
  selectionBaseHref,
  blocks,
  tree,
  requirements,
  components,
  externalArtifacts,
  tests,
  runs,
  links,
  artifactLinks,
  sysmlRelations,
  evidence,
}: TraceabilityGraphProps) {
  const raw = buildGraph({ blocks, tree, requirements, components, externalArtifacts, tests, runs, links, artifactLinks, sysmlRelations, evidence });
  const filtered = applyFocusAndSelection(raw, focus, selectedNodeId ?? null);

  if (!filtered.nodes.length) {
    return (
      <EmptyState
        title="No graph data available"
        description="The relationship explorer becomes useful as soon as the project has requirements, blocks, parts, tests, or evidence."
      />
    );
  }

  const counts = countKinds(filtered.nodes);
  const visibleKinds = laneOrder.filter((kind) => counts[kind] > 0);
  const selectedNode = selectedNodeId ? filtered.nodes.find((node) => node.id === selectedNodeId) : null;
  const selectedNodeLabel = selectedNode?.label ?? "";

  const incomingByNode = new Map<string, GraphEdge[]>();
  const outgoingByNode = new Map<string, GraphEdge[]>();
  for (const edge of filtered.edges) {
    if (!outgoingByNode.has(edge.source)) outgoingByNode.set(edge.source, []);
    if (!incomingByNode.has(edge.target)) incomingByNode.set(edge.target, []);
    outgoingByNode.get(edge.source)?.push(edge);
    incomingByNode.get(edge.target)?.push(edge);
  }

  const connectivity = new Map<string, { degree: number; kinds: Set<GraphKind> }>();
  for (const edge of filtered.edges) {
    const source = filtered.nodes.find((node) => node.id === edge.source);
    const target = filtered.nodes.find((node) => node.id === edge.target);
    if (!source || !target) continue;
    const sourceStats = connectivity.get(source.id) || { degree: 0, kinds: new Set<GraphKind>() };
    const targetStats = connectivity.get(target.id) || { degree: 0, kinds: new Set<GraphKind>() };
    sourceStats.degree += 1;
    targetStats.degree += 1;
    sourceStats.kinds.add(target.kind);
    targetStats.kinds.add(source.kind);
    connectivity.set(source.id, sourceStats);
    connectivity.set(target.id, targetStats);
  }

  const widthClass = visibleKinds.length > 3 ? "xl:grid-cols-2 2xl:grid-cols-3" : "xl:grid-cols-1";

  if (selectedNode) {
    const focusGraph = buildFocusedLayout(filtered, selectedNodeId ?? null);
    return (
      <Card>
        <CardBody className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {laneOrder.map((kind) => (
              <div key={kind} className={`rounded-2xl border ${kindMeta[kind].border} ${kindMeta[kind].fill} p-3`}>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">{kindMeta[kind].label}</div>
                <div className="mt-2 text-2xl font-semibold">{counts[kind] || 0}</div>
              </div>
            ))}
          </div>

          <div className="rounded-3xl border border-line bg-panel2/80 p-4">
            <div className="mb-4 flex flex-wrap gap-2">
              <Badge tone="accent">Focused graph</Badge>
              <Badge tone="neutral">Direct and indirect links</Badge>
              <Badge tone="warning">Click another box to refocus</Badge>
            </div>
            <div className="mb-4 rounded-2xl border border-dashed border-line bg-panel px-4 py-3 text-sm text-muted">
              Showing the connected graph for <span className="font-semibold text-text">{selectedNode.label}</span>.
            </div>
            <div className="mb-4">
              <Link
                href={selectionBaseHref}
                className="inline-flex items-center rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent"
                prefetch={false}
              >
                Clear focus
              </Link>
            </div>
            <FocusedGraphCanvas layout={focusGraph} selectionBaseHref={selectionBaseHref} />
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardBody className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
          {laneOrder.map((kind) => (
            <div key={kind} className={`rounded-2xl border ${kindMeta[kind].border} ${kindMeta[kind].fill} p-3`}>
              <div className="text-xs uppercase tracking-[0.2em] text-muted">{kindMeta[kind].label}</div>
              <div className="mt-2 text-2xl font-semibold">{counts[kind] || 0}</div>
            </div>
          ))}
        </div>

        <div className="rounded-3xl border border-line bg-panel2/80 p-4">
          <div className="mb-4 flex flex-wrap gap-2">
            <Badge tone="accent">Requirements</Badge>
            <Badge tone="neutral">Blocks</Badge>
            <Badge tone="warning">Parts</Badge>
            <Badge tone="success">Tests</Badge>
            <Badge tone="neutral">Operational evidence</Badge>
            <Badge tone="warning">Verification evidence</Badge>
          </div>

          <div className="mb-4 rounded-2xl border border-dashed border-line bg-panel px-4 py-3 text-sm text-muted">
            {selectedNode
              ? `Showing the connected graph for ${selectedNodeLabel}. The graph is now a compact relationship explorer, not a dense line canvas.`
              : "The graph shows the full project network for the chosen focus. Click any box to isolate its connected network and reduce visual noise."}
          </div>

          {selectedNode ? (
            <div className="mb-4 rounded-2xl border border-accent/30 bg-accent/5 px-4 py-3 text-sm">
              <span className="font-semibold text-text">{selectedNodeLabel}</span>
              <span className="ml-2 text-muted">is the current focus object.</span>
              <Link
                href={selectionBaseHref}
                className="ml-3 rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent"
                prefetch={false}
              >
                Clear focus
              </Link>
            </div>
          ) : null}

          <div className={`grid gap-4 ${widthClass}`}>
            {visibleKinds.map((kind) => {
              const nodes = filtered.nodes
                .filter((node) => node.kind === kind)
                .sort((a, b) => compareNodes(a, b, connectivity));
              return (
                <section key={kind} className="rounded-3xl border border-line bg-panel p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-xs uppercase tracking-[0.2em] text-muted">{kindMeta[kind].label}</div>
                      <div className="text-lg font-semibold">{nodes.length} objects</div>
                    </div>
                    <Badge tone={kindMeta[kind].tone}>{kindMeta[kind].label}</Badge>
                  </div>
                  <div className="mt-4 space-y-3">
                    {nodes.map((node) => (
                      <GraphNodeCard
                        key={node.id}
                        node={node}
                        selected={node.id === selectedNodeId}
                        focusHref={`${selectionBaseHref}&selected=${encodeURIComponent(node.id)}`}
                        incoming={incomingByNode.get(node.id) || []}
                        outgoing={outgoingByNode.get(node.id) || []}
                        nodesById={new Map(filtered.nodes.map((item) => [item.id, item]))}
                      />
                    ))}
                  </div>
                </section>
              );
            })}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function GraphNodeCard({
  node,
  selected,
  focusHref,
  incoming,
  outgoing,
  nodesById,
}: {
  node: GraphNode;
  selected: boolean;
  focusHref: string;
  incoming: GraphEdge[];
  outgoing: GraphEdge[];
  nodesById: Map<string, GraphNode>;
}) {
  const meta = kindMeta[node.kind];
  const title = (
    <div className="flex items-start justify-between gap-3">
      <div className="space-y-1">
        <div className="text-sm font-semibold leading-tight">{node.label}</div>
        {node.subtitle ? <div className="text-xs text-muted">{node.subtitle}</div> : null}
      </div>
      <Badge tone={meta.tone}>{meta.label}</Badge>
    </div>
  );

  return (
    <div className={`rounded-2xl border ${meta.border} bg-panel2/95 px-4 py-3 ${selected ? "ring-2 ring-accent/70" : ""}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="space-y-1">
            {title}
            {node.detail ? <div className="text-xs text-muted">{node.detail}</div> : null}
            {node.status ? <div className="text-xs uppercase tracking-[0.2em] text-muted">{node.status}</div> : null}
          </div>
        </div>
        <div className="flex shrink-0 gap-2">
          <Link href={focusHref} prefetch={false} className="rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent">
            Focus
          </Link>
          {node.href ? (
            <Link href={node.href} className="rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent">
              Open detail
            </Link>
          ) : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <RelationBlock title="Incoming" edges={incoming} nodesById={nodesById} direction="incoming" />
        <RelationBlock title="Outgoing" edges={outgoing} nodesById={nodesById} direction="outgoing" />
      </div>
    </div>
  );
}

function RelationBlock({
  title,
  edges,
  nodesById,
  direction,
}: {
  title: string;
  edges: GraphEdge[];
  nodesById: Map<string, GraphNode>;
  direction: "incoming" | "outgoing";
}) {
  return (
    <div className="rounded-xl border border-line/80 bg-panel px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.24em] text-muted">
        {title} links
        <span className="ml-2 text-muted/70">({edges.length})</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {edges.length ? (
          edges.map((edge) => {
            const relatedId = direction === "outgoing" ? edge.target : edge.source;
            const related = nodesById.get(relatedId);
            const label = related ? related.label : relatedId;
            const href = related?.href;
            const relationLabel = direction === "outgoing" ? `${edge.relation} → ${label}` : `${label} ← ${edge.relation}`;
            const chip = (
              <span className="inline-flex max-w-full items-center gap-2 rounded-full border border-line bg-panel2 px-3 py-1 text-xs text-text">
                <Badge tone={edge.tone}>{edge.relation}</Badge>
                <span className="truncate">{relationLabel}</span>
              </span>
            );
            return href ? (
              <Link key={edge.id} href={href} className="max-w-full hover:border-accent/60" title={label}>
                {chip}
              </Link>
            ) : (
              <div key={edge.id} className="max-w-full">
                {chip}
              </div>
            );
          })
        ) : (
          <div className="text-sm text-muted">No direct {title.toLowerCase()} links.</div>
        )}
      </div>
    </div>
  );
}

interface FocusedLayoutNode extends GraphNode {
  x: number;
  y: number;
  side: "incoming" | "outgoing" | "center";
  order: number;
}

interface FocusedLayoutEdge {
  edge: GraphEdge;
  source: FocusedLayoutNode;
  target: FocusedLayoutNode;
  index: number;
  pairKey: string;
  pairIndex: number;
  pairSize: number;
  pairOffset: number;
  labelSlot: number;
}

interface FocusedLayout {
  incoming: FocusedLayoutNode[];
  outgoing: FocusedLayoutNode[];
  edges: FocusedLayoutEdge[];
  width: number;
  height: number;
  selectedNode: FocusedLayoutNode;
  incomingBoundaryX: number;
  outgoingBoundaryX: number;
  labelBandHeight: number;
  nodeHeight: number;
}

function buildFocusedLayout(graph: { nodes: GraphNode[]; edges: GraphEdge[] }, selectedNodeId: string | null): FocusedLayout {
  const selected = selectedNodeId ? graph.nodes.find((node) => node.id === selectedNodeId) : null;
  if (!selected) {
    return {
      incoming: [],
      outgoing: [],
      edges: [],
      width: 0,
      height: 0,
      selectedNode: { id: "", kind: "requirement", label: "", lane: 0, x: 0, y: 0, side: "center", order: 0 },
      incomingBoundaryX: 0,
      outgoingBoundaryX: 0,
      labelBandHeight: 0,
      nodeHeight: 0,
    };
  }

  const incomingEdges = graph.edges.filter((edge) => edge.target === selected.id);
  const outgoingEdges = graph.edges.filter((edge) => edge.source === selected.id);
  const directNodeIds = new Set<string>([
    ...incomingEdges.map((edge) => edge.source),
    ...outgoingEdges.map((edge) => edge.target),
  ]);

  const connectivity = new Map<string, { degree: number; kinds: Set<GraphKind> }>();
  for (const edge of graph.edges) {
    const source = graph.nodes.find((node) => node.id === edge.source);
    const target = graph.nodes.find((node) => node.id === edge.target);
    if (!source || !target) continue;
    const sourceStats = connectivity.get(source.id) || { degree: 0, kinds: new Set<GraphKind>() };
    const targetStats = connectivity.get(target.id) || { degree: 0, kinds: new Set<GraphKind>() };
    sourceStats.degree += 1;
    targetStats.degree += 1;
    sourceStats.kinds.add(target.kind);
    targetStats.kinds.add(source.kind);
    connectivity.set(source.id, sourceStats);
    connectivity.set(target.id, targetStats);
  }

  const neighborMap = new Map<string, { node: GraphNode; incoming: number; outgoing: number }>();
  for (const edge of incomingEdges) {
    const node = graph.nodes.find((item) => item.id === edge.source);
    if (!node) continue;
    const current = neighborMap.get(node.id) || { node, incoming: 0, outgoing: 0 };
    current.incoming += 1;
    neighborMap.set(node.id, current);
  }
  for (const edge of outgoingEdges) {
    const node = graph.nodes.find((item) => item.id === edge.target);
    if (!node) continue;
    const current = neighborMap.get(node.id) || { node, incoming: 0, outgoing: 0 };
    current.outgoing += 1;
    neighborMap.set(node.id, current);
  }

  const leftNodes = [...neighborMap.values()]
    .filter((entry) => entry.incoming >= entry.outgoing)
    .map((entry) => entry.node)
    .sort((a, b) => compareNodes(a, b, connectivity));

  const rightNodes = [...neighborMap.values()]
    .filter((entry) => entry.outgoing > entry.incoming)
    .map((entry) => entry.node)
    .sort((a, b) => compareNodes(a, b, connectivity));

  const nodeWidth = 240;
  const nodeHeight = 150;
  const padding = 72;
  const centerGap = 1080;
  const rowGap = 340;
  const maxRows = Math.max(leftNodes.length, rightNodes.length, 1);
  const baseCenterY = padding + ((maxRows - 1) * rowGap) / 2;

  const incomingBase = leftNodes.map((node, order) => ({
    ...node,
    x: padding,
    y: baseCenterY + (order - (leftNodes.length - 1) / 2) * rowGap,
    side: "incoming" as const,
    order,
  }));
  const outgoingBase = rightNodes.map((node, order) => ({
    ...node,
    x: padding + centerGap,
    y: baseCenterY + (order - (rightNodes.length - 1) / 2) * rowGap,
    side: "outgoing" as const,
    order,
  }));
  const selectedBase: FocusedLayoutNode = {
    ...selected,
    x: padding + centerGap / 2,
    y: baseCenterY,
    side: "center",
    order: 0,
  };

  const pairBuckets = new Map<string, { edge: GraphEdge; source: FocusedLayoutNode; target: FocusedLayoutNode }[]>();
  for (const edge of [...incomingEdges, ...outgoingEdges]) {
    const source = edge.source === selected.id
      ? selectedBase
      : incomingBase.find((node) => node.id === edge.source) || outgoingBase.find((node) => node.id === edge.source);
    const target = edge.target === selected.id
      ? selectedBase
      : incomingBase.find((node) => node.id === edge.target) || outgoingBase.find((node) => node.id === edge.target);
    if (!source || !target) continue;
    const pairKey = [edge.source, edge.target].sort().join("::");
    const bucket = pairBuckets.get(pairKey) || [];
    bucket.push({ edge, source, target });
    pairBuckets.set(pairKey, bucket);
  }

  const pairLookup = new Map<string, FocusedLayoutNode>([
    [selectedBase.id, selectedBase],
    ...incomingBase.map((node) => [node.id, node] as const),
    ...outgoingBase.map((node) => [node.id, node] as const),
  ]);
  const pairKeys = [...pairBuckets.keys()].sort((left, right) => {
    const [leftSource, leftTarget] = left.split("::");
    const [rightSource, rightTarget] = right.split("::");
    const leftSourceNode = pairLookup.get(leftSource);
    const leftTargetNode = pairLookup.get(leftTarget);
    const rightSourceNode = pairLookup.get(rightSource);
    const rightTargetNode = pairLookup.get(rightTarget);
    const leftLabel = `${leftSourceNode?.label || leftSource} -> ${leftTargetNode?.label || leftTarget}`;
    const rightLabel = `${rightSourceNode?.label || rightSource} -> ${rightTargetNode?.label || rightTarget}`;
    return leftLabel.localeCompare(rightLabel);
  });

  const totalEdgeCount = [...pairBuckets.values()].reduce((sum, bucket) => sum + bucket.length, 0);
  const labelBandHeight = Math.max(180, totalEdgeCount * 28 + 64);
  const incoming = incomingBase.map((node) => ({ ...node, y: node.y + labelBandHeight }));
  const outgoing = outgoingBase.map((node) => ({ ...node, y: node.y + labelBandHeight }));
  const selectedNode = { ...selectedBase, y: selectedBase.y + labelBandHeight };
  const positions = new Map<string, FocusedLayoutNode>([
    [selectedNode.id, selectedNode],
    ...incoming.map((node) => [node.id, node] as const),
    ...outgoing.map((node) => [node.id, node] as const),
  ]);
  const pairIndexByKey = new Map(pairKeys.map((key, index) => [key, index] as const));
  const edges = pairKeys.flatMap((pairKey) => {
    const bucket = pairBuckets.get(pairKey) || [];
    return bucket.map(({ edge, source, target }, index) => {
      const positionedSource = positions.get(edge.source) || source;
      const positionedTarget = positions.get(edge.target) || target;
      const pairIndex = pairIndexByKey.get(pairKey) ?? 0;
      const pairSize = bucket.length;
      const pairOffset = (pairIndex - (pairKeys.length - 1) / 2) * 72;
      return {
        edge,
        source: positionedSource,
        target: positionedTarget,
        index,
        pairKey,
        pairIndex,
        pairSize,
        pairOffset,
        labelSlot: index,
      };
    });
  });

  const width = padding * 2 + centerGap + nodeWidth;
  const height = padding * 2 + labelBandHeight + Math.max(leftNodes.length, rightNodes.length, 1) * rowGap + nodeHeight;

  return {
    incoming,
    outgoing,
    edges,
    width,
    height,
    selectedNode,
    incomingBoundaryX: padding + nodeWidth + 36,
    outgoingBoundaryX: padding + centerGap - 36,
    labelBandHeight,
    nodeHeight,
  };
}

function FocusedGraphCanvas({ layout, selectionBaseHref }: { layout: FocusedLayout; selectionBaseHref: string }) {
  const nodeWidth = 240;
  const nodeHeight = layout.nodeHeight || 150;
  const labelSlots = new Map<string, number>();
  const edgeSlots = layout.edges.map((item) => {
    const slot = labelSlots.get(item.pairKey) ?? 0;
    labelSlots.set(item.pairKey, slot + 1);
    return { ...item, labelSlot: slot };
  });

  return (
    <div className="overflow-x-auto pb-2">
      <div className="relative min-w-[980px]" style={{ width: layout.width, height: layout.height }}>
        <div className="absolute inset-y-0" style={{ left: layout.incomingBoundaryX }}>
          <div className="h-full border-l border-dashed border-white/10" />
        </div>
        <div className="absolute inset-y-0" style={{ left: layout.outgoingBoundaryX }}>
          <div className="h-full border-l border-dashed border-white/10" />
        </div>
        <div className="absolute left-3 top-3 rounded-full border border-line bg-panel/90 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-muted">
          Incoming
        </div>
        <div className="absolute left-1/2 top-3 -translate-x-1/2 rounded-full border border-accent/30 bg-accent/5 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-accent">
          Focus
        </div>
        <div className="absolute right-3 top-3 rounded-full border border-line bg-panel/90 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-muted">
          Outgoing
        </div>
        <svg aria-hidden className="absolute inset-0 h-full w-full">
          {edgeSlots.map(({ edge, source, target, pairOffset, pairSize, labelSlot, pairIndex }) => {
            const startX = source.x + nodeWidth;
            const endX = target.x;
            const startY = source.y + nodeHeight / 2;
            const endY = target.y + nodeHeight / 2;
            const duplicateBoost = pairSize > 1 ? (pairSize - 1) * 26 : 0;
            const intraOffset = (labelSlot - (pairSize - 1) / 2) * (pairSize > 1 ? 56 : 34);
            const offset = pairOffset + intraOffset;
            const bend = 280 + pairIndex * 48 + labelSlot * 24 + duplicateBoost;
            const controlLeft = startX + bend;
            const controlRight = endX - bend;
            const path = `M ${startX} ${startY} C ${controlLeft} ${startY + offset}, ${controlRight} ${endY - offset}, ${endX} ${endY}`;
            const label = relationExplanation(edge.relation, source.kind, target.kind);
            const mid = cubicPoint(
              startX,
              startY,
              controlLeft,
              startY + offset,
              controlRight,
              endY - offset,
              endX,
              endY,
              0.5,
            );
            const tangent = cubicTangent(
              startX,
              startY,
              controlLeft,
              startY + offset,
              controlRight,
              endY - offset,
              endX,
              endY,
              0.5,
            );
            const normalLength = Math.max(1, Math.hypot(-tangent.y, tangent.x));
            const normalX = -tangent.y / normalLength;
            const normalY = tangent.x / normalLength;
            const duplicateShift = (labelSlot - (pairSize - 1) / 2) * (pairSize > 1 ? 20 : 8);
            const labelX = mid.x + normalX * (22 + duplicateShift);
            const labelY = mid.y + normalY * (22 + duplicateShift);
            return (
              <g key={edge.id}>
                <path d={path} fill="none" stroke="rgba(15,23,42,0.88)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
                <path
                  d={path}
                  fill="none"
                  stroke={edgeStroke(edge.tone)}
                  strokeWidth="2.75"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity="0.95"
                  strokeDasharray={edge.tone === "warning" ? "6 6" : edge.tone === "neutral" ? "4 6" : undefined}
                />
                <rect
                  x={labelX - Math.max(52, label.length * 3.2)}
                  y={labelY - 10}
                  width={Math.max(104, label.length * 6.4)}
                  height={20}
                  rx="999"
                  fill="rgba(15,23,42,0.92)"
                  opacity="0.88"
                />
                <text
                  x={labelX}
                  y={labelY + 4}
                  textAnchor="middle"
                  className="fill-text text-[10px] font-medium uppercase tracking-[0.18em]"
                  stroke="rgba(15,23,42,0.95)"
                  strokeWidth="4"
                  paintOrder="stroke fill"
                >
                  {label}
                </text>
              </g>
            );
          })}
        </svg>

        {layout.incoming.map((node) => (
          <FocusedGraphNodeCard
            key={node.id}
            node={node}
            selected={false}
            focusHref={`${selectionBaseHref}&selected=${encodeURIComponent(node.id)}`}
          />
        ))}
        <FocusedGraphNodeCard node={layout.selectedNode} selected focusHref={selectionBaseHref} />
        {layout.outgoing.map((node) => (
          <FocusedGraphNodeCard
            key={node.id}
            node={node}
            selected={false}
            focusHref={`${selectionBaseHref}&selected=${encodeURIComponent(node.id)}`}
          />
        ))}
      </div>
    </div>
  );
}

function FocusedGraphNodeCard({ node, selected, focusHref }: { node: FocusedLayoutNode; selected: boolean; focusHref: string }) {
  const meta = kindMeta[node.kind];
  return (
    <div
      className={`absolute rounded-2xl border ${meta.border} bg-panel/96 px-4 py-3 shadow-sm backdrop-blur-sm ${selected ? "ring-2 ring-accent/80" : ""}`}
      style={{ left: node.x, top: node.y, width: 240, height: 150 }}
    >
      {node.side !== "outgoing" ? (
        <div className="pointer-events-none absolute left-0 top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border border-line bg-panel2 shadow-sm" />
      ) : null}
      {node.side !== "incoming" ? (
        <div className="pointer-events-none absolute right-0 top-1/2 h-4 w-4 translate-x-1/2 -translate-y-1/2 rounded-full border border-line bg-panel2 shadow-sm" />
      ) : null}
      <div className="flex h-full flex-col justify-between gap-3">
        <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold leading-tight">{node.label}</div>
          {node.subtitle ? <div className="mt-1 text-xs text-muted">{node.subtitle}</div> : null}
          {node.detail ? <div className="mt-2 text-xs text-muted">{node.detail}</div> : null}
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
        </div>
        <div>
          {node.status ? <div className="mt-2 text-xs uppercase tracking-[0.2em] text-muted">{node.status}</div> : null}
          <div className="mt-3 flex flex-wrap gap-2">
            <Link href={focusHref} prefetch={false} className="rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent">
              Focus
            </Link>
            {node.href ? (
              <Link href={node.href} className="rounded-full border border-line px-3 py-1 text-xs text-text hover:border-accent/60 hover:text-accent">
                Open detail
              </Link>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

function cubicPoint(
  x1: number,
  y1: number,
  cx1: number,
  cy1: number,
  cx2: number,
  cy2: number,
  x2: number,
  y2: number,
  t: number,
) {
  const mt = 1 - t;
  const mt2 = mt * mt;
  const t2 = t * t;
  const x =
    mt2 * mt * x1 +
    3 * mt2 * t * cx1 +
    3 * mt * t2 * cx2 +
    t2 * t * x2;
  const y =
    mt2 * mt * y1 +
    3 * mt2 * t * cy1 +
    3 * mt * t2 * cy2 +
    t2 * t * y2;
  return { x, y };
}

function cubicTangent(
  x1: number,
  y1: number,
  cx1: number,
  cy1: number,
  cx2: number,
  cy2: number,
  x2: number,
  y2: number,
  t: number,
) {
  const mt = 1 - t;
  const x =
    3 * mt * mt * (cx1 - x1) +
    6 * mt * t * (cx2 - cx1) +
    3 * t * t * (x2 - cx2);
  const y =
    3 * mt * mt * (cy1 - y1) +
    6 * mt * t * (cy2 - cy1) +
    3 * t * t * (y2 - cy2);
  return { x, y };
}

function buildGraph({
  blocks,
  tree,
  requirements,
  components,
  externalArtifacts,
  tests,
  runs,
  links,
  artifactLinks,
  sysmlRelations,
  evidence,
}: Omit<TraceabilityGraphProps, "focus" | "selectedNodeId" | "selectionBaseHref">): { nodes: GraphNode[]; edges: GraphEdge[] } {
  const nodes = new Map<string, GraphNode>();
  const edges = new Map<string, GraphEdge>();

  const addNode = (node: GraphNode) => {
    if (!nodes.has(node.id)) nodes.set(node.id, node);
  };

  const addEdge = (edge: GraphEdge) => {
    if (!nodes.has(edge.source) || !nodes.has(edge.target)) return;
    const edgeKey = `${edge.source}->${edge.target}`;
    if (!edges.has(edgeKey)) edges.set(edgeKey, edge);
  };

  for (const requirement of requirements) {
    addNode({
      id: `requirement:${requirement.id}`,
      kind: "requirement",
      label: requirement.key,
      subtitle: requirement.title,
      href: `/requirements/${requirement.id}`,
      status: requirement.status,
      detail: requirement.priority,
      lane: 0,
    });
  }

  const addBlock = (block: Block) => {
    addNode({
      id: `block:${block.id}`,
      kind: "block",
      label: block.key,
      subtitle: block.name,
      href: `/blocks/${block.id}`,
      status: block.abstraction_level,
      detail: block.block_kind,
      lane: 1,
    });
  };

  if (tree.length) {
    const visit = (node: BlockTreeNode, parentId?: string) => {
      const blockId = `block:${node.block.id}`;
      addBlock(node.block);
      if (parentId) {
        addEdge({ id: `${parentId}->${blockId}::contains`, source: parentId, target: blockId, relation: "contains", tone: relationTone.contains });
      }
      for (const req of node.satisfied_requirements || []) {
        const reqId = `requirement:${req.object_id}`;
        addEdge({ id: `${blockId}->${reqId}::satisfies`, source: blockId, target: reqId, relation: "satisfies", tone: relationTone.satisfies });
      }
      for (const test of node.linked_tests || []) {
        const testId = `test_case:${test.object_id}`;
        addEdge({ id: `${blockId}->${testId}::verify`, source: blockId, target: testId, relation: "verify", tone: relationTone.verify });
      }
      for (const child of node.children || []) {
        visit(child, blockId);
      }
    };
    tree.forEach((root) => visit(root));
  }

  for (const block of blocks) addBlock(block);

  for (const component of components) {
    addNode({
      id: `component:${component.id}`,
      kind: "component",
      label: component.key,
      subtitle: component.name,
      href: `/components/${component.id}`,
      status: component.status,
      detail: component.type,
      lane: 2,
    });
  }

  for (const artifact of externalArtifacts) {
    addNode({
      id: `external_artifact:${artifact.id}`,
      kind: "external_artifact",
      label: artifact.external_id,
      subtitle: artifact.name,
      href: `/external-artifacts/${artifact.id}`,
      status: artifact.status,
      detail: artifact.artifact_type,
      lane: 3,
    });
  }

  for (const test of tests) {
    addNode({
      id: `test_case:${test.id}`,
      kind: "test_case",
      label: test.key,
      subtitle: test.title,
      href: `/test-cases/${test.id}`,
      status: test.status,
      detail: test.method,
      lane: 3,
    });
  }

  for (const run of runs) {
    addNode({
      id: `operational_run:${run.id}`,
      kind: "operational_run",
      label: run.key,
      subtitle: run.notes || run.location,
      href: `/operational-runs/${run.id}`,
      status: run.outcome,
      detail: `${run.location} • ${run.date}`,
      lane: 4,
    });
  }

  for (const item of evidence) {
    addNode({
      id: `verification_evidence:${item.id}`,
      kind: "verification_evidence",
      label: item.title,
      subtitle: item.source_name || item.evidence_type,
      status: item.evidence_type,
      detail: item.source_reference || item.summary,
      lane: 5,
    });
    for (const linked of item.linked_objects || []) {
      const targetKind = linkedObjectKind(linked.object_type);
      if (!targetKind) continue;
      addEdge({
        id: `verification_evidence:${item.id}->${targetKind}:${linked.object_id}::evidence_of`,
        source: `verification_evidence:${item.id}`,
        target: `${targetKind}:${linked.object_id}`,
        relation: "evidence_of",
        tone: relationTone.evidence_of,
      });
    }
  }

  for (const rel of sysmlRelations) {
    const sourceKind = sysmlKind(rel.source_type);
    const targetKind = sysmlKind(rel.target_type);
    if (!sourceKind || !targetKind) continue;
    addEdge({
      id: `${sourceKind}:${rel.source_id}->${targetKind}:${rel.target_id}::${rel.relation_type}`,
      source: `${sourceKind}:${rel.source_id}`,
      target: `${targetKind}:${rel.target_id}`,
      relation: rel.relation_type,
      tone: relationTone[rel.relation_type] ?? "accent",
    });
  }

  for (const link of links) {
    const sourceKind = linkKind(link.source_type);
    const targetKind = linkKind(link.target_type);
    if (!sourceKind || !targetKind) continue;
    addEdge({
      id: `${sourceKind}:${link.source_id}->${targetKind}:${link.target_id}::${link.relation_type}`,
      source: `${sourceKind}:${link.source_id}`,
      target: `${targetKind}:${link.target_id}`,
      relation: link.relation_type,
      tone: relationTone[link.relation_type] ?? "warning",
    });
  }

  for (const link of artifactLinks) {
    const internalKind = federatedKind(link.internal_object_type);
    if (!internalKind) continue;
    const sourceId = `${internalKind}:${link.internal_object_id}`;
    const targetId = `external_artifact:${link.external_artifact_id}`;
    if (!nodes.has(sourceId) || !nodes.has(targetId)) continue;
    addEdge({
      id: `${sourceId}->${targetId}::artifact_${link.relation_type}`,
      source: sourceId,
      target: targetId,
      relation: link.relation_type,
      tone: relationTone[link.relation_type] ?? "accent",
    });
  }

  return { nodes: [...nodes.values()], edges: [...edges.values()] };
}

function applyFocusAndSelection(graph: { nodes: GraphNode[]; edges: GraphEdge[] }, focus: GraphFocus, selectedNodeId: string | null) {
  const focused = filterGraph(graph, focus);
  if (!selectedNodeId || !focused.nodes.some((node) => node.id === selectedNodeId)) return focused;

  const adjacency = new Map<string, Set<string>>();
  for (const edge of focused.edges) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, new Set<string>());
    if (!adjacency.has(edge.target)) adjacency.set(edge.target, new Set<string>());
    adjacency.get(edge.source)?.add(edge.target);
    adjacency.get(edge.target)?.add(edge.source);
  }

  const included = new Set<string>([selectedNodeId]);
  const queue = [selectedNodeId];
  while (queue.length) {
    const current = queue.shift()!;
    for (const next of adjacency.get(current) || []) {
      if (included.has(next)) continue;
      included.add(next);
      queue.push(next);
    }
  }

  return {
    nodes: focused.nodes.filter((node) => included.has(node.id)),
    edges: focused.edges.filter((edge) => included.has(edge.source) && included.has(edge.target)),
  };
}

function filterGraph(graph: { nodes: GraphNode[]; edges: GraphEdge[] }, focus: GraphFocus) {
  if (focus === "all") return graph;
  const seedKinds = focusKinds[focus];
  const allowedRelations = new Set(focusRelations[focus]);
  const seedIds = new Set(graph.nodes.filter((node) => seedKinds.includes(node.kind)).map((node) => node.id));
  const included = new Set(seedIds);
  const edges = graph.edges.filter((edge) => {
    if (!allowedRelations.has(edge.relation)) return false;
    if (!seedIds.has(edge.source) && !seedIds.has(edge.target)) return false;
    included.add(edge.source);
    included.add(edge.target);
    return true;
  });
  return {
    nodes: graph.nodes.filter((node) => included.has(node.id)),
    edges,
  };
}

function countKinds(nodes: GraphNode[]) {
  return laneOrder.reduce<Record<GraphKind, number>>((acc, kind) => {
    acc[kind] = nodes.filter((node) => node.kind === kind).length;
    return acc;
  }, {} as Record<GraphKind, number>);
}

function edgeStroke(tone: GraphTone) {
  if (tone === "success") return "#34d399";
  if (tone === "warning") return "#f59e0b";
  if (tone === "danger") return "#fb7185";
  if (tone === "neutral") return "#94a3b8";
  return "#7dd3fc";
}

function compareNodes(
  left: GraphNode,
  right: GraphNode,
  connectivity: Map<string, { degree: number; kinds: Set<GraphKind> }>,
) {
  const leftStats = connectivity.get(left.id) || { degree: 0, kinds: new Set<GraphKind>() };
  const rightStats = connectivity.get(right.id) || { degree: 0, kinds: new Set<GraphKind>() };
  if (rightStats.degree !== leftStats.degree) return rightStats.degree - leftStats.degree;
  if (rightStats.kinds.size !== leftStats.kinds.size) return rightStats.kinds.size - leftStats.kinds.size;
  return left.label.localeCompare(right.label);
}

function relationExplanation(relation: string, sourceKind: GraphKind, targetKind: GraphKind) {
  if (relation === "satisfies" || relation === "satisfy") return "Requirement coverage";
  if (relation === "verifies" || relation === "verify") return "Verification evidence";
  if (relation === "contains" || relation === "contain") return "Structural containment";
  if (relation === "deriveReqt") return "Derived requirement";
  if (relation === "allocate" || relation === "allocated_to") return "Allocated realization";
  if (relation === "maps_to") return "Mapped external reference";
  if (relation === "authoritative_reference") return "Authoritative reference";
  if (relation === "validated_against") return "Validated against external source";
  if (relation === "synchronized_with") return "Synchronized external source";
  if (relation === "derived_from_external") return "Derived external source";
  if (relation === "refine") return "Refinement link";
  if (relation === "reports_on") return "Operational evidence";
  if (relation === "evidence_of") return "Reusable evidence";
  if (relation === "trace") return "Trace relation";
  return `${kindMeta[sourceKind].label} to ${kindMeta[targetKind].label}`;
}

function sysmlKind(kind: string) {
  if (kind === "requirement") return "requirement";
  if (kind === "block") return "block";
  if (kind === "component") return "component";
  if (kind === "test_case") return "test_case";
  if (kind === "operational_run") return "operational_run";
  return null;
}

function linkKind(kind: string) {
  if (kind === "requirement") return "requirement";
  if (kind === "component") return "component";
  if (kind === "test_case") return "test_case";
  if (kind === "operational_run") return "operational_run";
  return null;
}

function linkedObjectKind(kind: string) {
  if (kind === "requirement") return "requirement";
  if (kind === "component") return "component";
  if (kind === "test_case") return "test_case";
  return null;
}

function federatedKind(kind: string) {
  if (kind === "requirement") return "requirement";
  if (kind === "block") return "block";
  if (kind === "component") return "component";
  if (kind === "test_case") return "test_case";
  return null;
}
