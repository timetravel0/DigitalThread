import Link from "next/link";
import { Badge, Card, CardBody, EmptyState } from "@/components/ui";
import type {
  Block,
  BlockTreeNode,
  Component,
  Link as TraceLink,
  OperationalRun,
  Requirement,
  SysMLRelation,
  TestCase,
  VerificationEvidence,
} from "@/lib/types";

type GraphFocus = "all" | "requirements" | "blocks" | "parts" | "tests" | "evidence";
type GraphKind = "requirement" | "block" | "component" | "test_case" | "operational_run" | "verification_evidence";
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
  blocks: Block[];
  tree: BlockTreeNode[];
  requirements: Requirement[];
  components: Component[];
  tests: TestCase[];
  runs: OperationalRun[];
  links: TraceLink[];
  sysmlRelations: SysMLRelation[];
  evidence: VerificationEvidence[];
}

const laneOrder: GraphKind[] = ["requirement", "block", "component", "test_case", "operational_run", "verification_evidence"];

const focusKinds: Record<GraphFocus, GraphKind[]> = {
  all: laneOrder,
  requirements: ["requirement"],
  blocks: ["block"],
  parts: ["component"],
  tests: ["test_case"],
  evidence: ["operational_run", "verification_evidence"],
};

const kindMeta: Record<GraphKind, { label: string; tone: GraphTone; border: string; fill: string }> = {
  requirement: { label: "Requirement", tone: "accent", border: "border-sky-400/40", fill: "bg-sky-500/10" },
  block: { label: "Block", tone: "neutral", border: "border-cyan-400/40", fill: "bg-cyan-500/10" },
  component: { label: "Part", tone: "warning", border: "border-amber-400/40", fill: "bg-amber-500/10" },
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
  verifies: "success",
  reports_on: "neutral",
  evidence_of: "warning",
};

export function TraceabilityGraph({
  focus,
  blocks,
  tree,
  requirements,
  components,
  tests,
  runs,
  links,
  sysmlRelations,
  evidence,
}: TraceabilityGraphProps) {
  const raw = buildGraph({ blocks, tree, requirements, components, tests, runs, links, sysmlRelations, evidence });
  const filtered = filterGraph(raw, focus);

  if (!filtered.nodes.length) {
    return (
      <EmptyState
        title="No graph data available"
        description="The traceability graph is usable even before the project is populated. Create requirements, blocks, parts, tests, or evidence and they will appear here."
      />
    );
  }

  const counts = countKinds(filtered.nodes);
  const visibleKinds = laneOrder.filter((kind) => counts[kind] > 0);
  const laneWidth = 280;
  const nodeWidth = 232;
  const nodeHeight = 104;
  const rowGap = 136;
  const laneCount = Math.max(visibleKinds.length, 1);
  const width = laneCount * laneWidth + 48;
  const laneMap = new Map<GraphKind, number>(visibleKinds.map((kind, index) => [kind, index]));
  const nodesByLane = visibleKinds.map((kind) =>
    filtered.nodes
      .filter((node) => node.kind === kind)
      .sort((a, b) => a.label.localeCompare(b.label))
      .map((node, index) => ({
        ...node,
        laneIndex: laneMap.get(kind) ?? 0,
        x: (laneMap.get(kind) ?? 0) * laneWidth + 24,
        y: index * rowGap + 64,
      }))
  );
  const flatNodes = nodesByLane.flat();
  const nodePositions = new Map(flatNodes.map((node) => [node.id, node]));
  const height = Math.max(...nodesByLane.map((lane) => lane.length), 1) * rowGap + 160;

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

          <div className="overflow-x-auto pb-2">
            <div className="relative min-w-[1180px]" style={{ width, height }}>
              <svg aria-hidden className="absolute inset-0 h-full w-full">
                {filtered.edges.map((edge) => {
                  const source = nodePositions.get(edge.source);
                  const target = nodePositions.get(edge.target);
                  if (!source || !target) return null;
                  const x1 = source.x + nodeWidth;
                  const y1 = source.y + nodeHeight / 2;
                  const x2 = target.x;
                  const y2 = target.y + nodeHeight / 2;
                  const curve = `M ${x1} ${y1} C ${x1 + 70} ${y1}, ${x2 - 70} ${y2}, ${x2} ${y2}`;
                  const stroke = edgeStroke(edge.tone);
                  return <path key={edge.id} d={curve} fill="none" stroke={stroke} strokeWidth="2" strokeDasharray={edge.tone === "warning" ? "6 6" : edge.tone === "neutral" ? "4 6" : undefined} opacity="0.85" />;
                })}
              </svg>

              {visibleKinds.map((kind, laneIndex) => {
                const laneNodes = flatNodes.filter((node) => node.kind === kind);
                const laneX = laneIndex * laneWidth + 24;
                return (
                  <div key={kind} className="absolute top-0" style={{ left: laneX, width: nodeWidth }}>
                    <div className={`mb-3 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${kindMeta[kind].border} ${kindMeta[kind].fill} text-text`}>
                      {kindMeta[kind].label}
                    </div>
                    {laneNodes.map((node) => (
                      <GraphNodeCard key={node.id} node={node} width={nodeWidth} />
                    ))}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function GraphNodeCard({ node, width }: { node: GraphNode & { x: number; y: number }; width: number }) {
  const meta = kindMeta[node.kind];
  const isLink = Boolean(node.href);
  const content = (
    <div
      className={`absolute rounded-2xl border ${meta.border} ${meta.fill} px-4 py-3 shadow-sm`}
      style={{ left: node.x, top: node.y, width }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold leading-tight">{node.label}</div>
          {node.subtitle ? <div className="mt-1 text-xs text-muted">{node.subtitle}</div> : null}
        </div>
        <Badge tone={meta.tone}>{meta.label}</Badge>
      </div>
      {node.detail ? <div className="mt-2 text-xs text-muted">{node.detail}</div> : null}
      {node.status ? <div className="mt-2 text-xs uppercase tracking-[0.2em] text-muted">{node.status}</div> : null}
    </div>
  );

  if (!isLink) return content;

  return (
    <Link href={node.href as string} className="group">
      {content}
    </Link>
  );
}

function buildGraph({
  blocks,
  tree,
  requirements,
  components,
  tests,
  runs,
  links,
  sysmlRelations,
  evidence,
}: Omit<TraceabilityGraphProps, "projectId" | "focus">): { nodes: GraphNode[]; edges: GraphEdge[] } {
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

  for (const block of blocks) {
    addBlock(block);
  }

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

  return { nodes: [...nodes.values()], edges: [...edges.values()] };
}

function filterGraph(graph: { nodes: GraphNode[]; edges: GraphEdge[] }, focus: GraphFocus) {
  if (focus === "all") return graph;
  const seedKinds = focusKinds[focus];
  const included = new Set(graph.nodes.filter((node) => seedKinds.includes(node.kind)).map((node) => node.id));
  let changed = true;
  while (changed) {
    changed = false;
    for (const edge of graph.edges) {
      const touches = included.has(edge.source) || included.has(edge.target);
      if (!touches) continue;
      if (!included.has(edge.source)) {
        included.add(edge.source);
        changed = true;
      }
      if (!included.has(edge.target)) {
        included.add(edge.target);
        changed = true;
      }
    }
  }
  return {
    nodes: graph.nodes.filter((node) => included.has(node.id)),
    edges: graph.edges.filter((edge) => included.has(edge.source) && included.has(edge.target)),
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
