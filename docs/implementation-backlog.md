# Implementation Backlog

Epic A is already implemented and treated as the foundation. The backlog below starts at Epic B.

## Epic B: Global Configuration & Baselines

### B1 - Configuration context comparison

- Description: Add a compare endpoint and UI for two configuration contexts or baselines.
- Why it matters: aerospace review gates need a deterministic way to see what changed between approved states.
- Dependencies: existing configuration contexts and baselines.
- Acceptance criteria: users can select two contexts and see added, removed, and version-changed items by type.
- Suggested test coverage: diff service tests, API shape tests, UI snapshot tests.
- Complexity: M

### B2 - Frozen context immutability

- Description: Enforce immutability for frozen, released, and obsolete configuration contexts.
- Why it matters: review gates are only credible if they cannot be silently altered.
- Dependencies: configuration contexts.
- Acceptance criteria: edits and mapping changes are rejected for frozen contexts; the UI hides edit actions.
- Suggested test coverage: transition tests, validation tests, UI conditional rendering tests.
- Complexity: S

### B3 - Baseline-to-context bridge

- Description: Let a baseline be surfaced as one specific kind of configuration context without changing the baseline model.
- Why it matters: preserves the current baseline feature while giving the product a clearer configuration story.
- Dependencies: B1.
- Acceptance criteria: users can navigate from a baseline to its related context and compare it with another context.
- Suggested test coverage: route tests, seed checks, workspace rendering tests.
- Complexity: S

## Epic C: Verification Evidence & Closed Loop

### C1 - Verification evidence model

- Description: Add `VerificationEvidence` as a first-class object linked to requirements, tests, simulation runs, and telemetry.
- Why it matters: evidence must be reusable, reviewable, and distinct from raw execution records.
- Dependencies: none.
- Acceptance criteria: evidence can be created, listed, linked, and exported.
- Suggested test coverage: CRUD tests, relation tests, export tests.
- Complexity: L

### C2 - Requirement verification status engine

- Description: Derive requirement verification state from linked evidence using a small rule set.
- Why it matters: the dashboard should reflect engineering reality, not just authored approval status.
- Dependencies: C1.
- Acceptance criteria: requirements resolve to `verified`, `partially_verified`, `at_risk`, `failed`, or `not_covered`.
- Suggested test coverage: rule matrix tests, edge-case tests, regression tests.
- Complexity: M

### C3 - Simulation evidence records

- Status: Implemented in the current codebase.
- Description: Add simulation-specific evidence records for model, scenario, input, and result capture.
- Why it matters: simulation feedback needs its own semantics instead of hiding inside test runs.
- Dependencies: C1.
- Acceptance criteria: simulation evidence can be linked to requirements and shown in the UI.
- Suggested test coverage: schema tests, service tests, UI detail tests.
- Complexity: M

### C4 - Operational evidence batches

- Status: Implemented in the current codebase.
- Description: Add operational or telemetry evidence batches that can be reviewed and attached to verification claims.
- Why it matters: closed-loop feedback needs a stable ingestion shape without a streaming platform.
- Dependencies: C1.
- Acceptance criteria: operational data can be attached to evidence and summarized by requirement.
- Suggested test coverage: ingestion tests, linkage tests, status update tests.
- Complexity: M

## Epic D: Aerospace Traceability Enrichment

### D1 - Logical vs physical view cues

- Description: Clarify logical architecture versus physical realization in the UI and seeded demo.
- Why it matters: the drone scenario needs a clearer aerospace narrative than a generic block list.
- Dependencies: existing block/component data.
- Acceptance criteria: users can tell when a node is logical, physical, or software-related.
- Suggested test coverage: rendering tests, seed validation tests.
- Complexity: S

### D2 - Software realization traceability

- Description: Introduce an optional `SoftwareModule` or equivalent software realization surface.
- Why it matters: flight software should be traceable as a distinct realization, not only as a block type.
- Dependencies: D1.
- Acceptance criteria: software artifacts can be linked to requirements, blocks, and evidence.
- Suggested test coverage: model tests, API tests, detail page tests.
- Complexity: M

### D3 - Traceability graph view

- Description: Add a graph or node-link view for requirements, blocks, parts, tests, evidence, and changes.
- Why it matters: connectivity is easier to explain when the relationships are visible as a graph.
- Dependencies: existing trace data.
- Acceptance criteria: users can inspect connected objects and relation types from a graph view.
- Suggested test coverage: data shaping tests, UI snapshot tests, empty-state tests.
- Complexity: M

### D4 - Graph-aware impact traversal

- Description: Replace narrow impact traversal with a graph-aware service that can cross the broader domain model.
- Why it matters: impact analysis should follow the same connectivity model as the rest of the product.
- Dependencies: D3, C1.
- Acceptance criteria: impact output includes requirements, realization objects, tests, evidence, and open changes where relevant.
- Suggested test coverage: traversal tests, cycle-handling tests, regression tests.
- Complexity: L

## Epic E: Non-Conformity & Change

### E1 - Non-conformity entity

- Description: Add `NonConformity` as a first-class object linked to evidence and impacted assets.
- Why it matters: issue management and change management are not the same thing.
- Dependencies: C1.
- Acceptance criteria: NCRs can be created, listed, linked, and traced to evidence.
- Suggested test coverage: CRUD tests, relation tests, detail page tests.
- Complexity: M

### E2 - Change lifecycle expansion

- Description: Expand change requests into a traceable lifecycle with analysis, disposition, implementation, and closure.
- Why it matters: aerospace change control needs explicit state transitions and approvals.
- Dependencies: E1, B1.
- Acceptance criteria: change requests move through valid states and retain audit history.
- Suggested test coverage: transition tests, invalid-state tests, audit tests.
- Complexity: M

### E3 - Audit reuse across decision objects

- Description: Reuse the approval audit pattern for contexts, baselines, changes, and non-conformities.
- Why it matters: decision history must be consistent across the product.
- Dependencies: E2.
- Acceptance criteria: each state transition writes a traceable decision record.
- Suggested test coverage: audit row tests, actor/comment tests.
- Complexity: S

## Epic F: Connector Framework & Standards Contracts

### F1 - JSON and CSV importer

- Status: Implemented in the current codebase.
- Description: Add simple import endpoints for external tool exports in JSON or CSV form.
- Why it matters: it is the fastest practical path to demonstrate external federation without live integrations.
- Dependencies: existing connector and external artifact models.
- Acceptance criteria: imported payloads create or update external artifacts and versions.
- Suggested test coverage: parsing tests, validation tests, round-trip tests.
- Complexity: M

### F2 - SysML v2 mapping contract

- Status: Implemented in the current codebase.
- Description: Add a mapping layer from the current internal model to SysML v2-shaped concepts.
- Why it matters: it gives the product a standards-aware path without pretending to be native SysML v2.
- Dependencies: D1.
- Acceptance criteria: requirement, block, satisfy, verify, and derive mappings are explicit.
- Suggested test coverage: mapping tests, API shape tests.
- Complexity: M

### F3 - STEP AP242 placeholder contract

- Status: Implemented in the current codebase.
- Description: Add a lightweight exchange contract for part metadata aligned to STEP AP242 semantics.
- Why it matters: physical part linkage becomes more credible when the exchange shape is named.
- Dependencies: existing external artifact model.
- Acceptance criteria: the API can store and export a placeholder AP242-style payload.
- Suggested test coverage: schema tests, export tests.
- Complexity: S

### F4 - FMI placeholder contract

- Status: implemented

- Description: Add a lightweight exchange contract for model and simulation metadata aligned to FMI semantics.
- Why it matters: simulation credibility improves when the exchange concept is explicit.
- Dependencies: C3.
- Acceptance criteria: simulation evidence can reference an FMI-like contract record.
- Suggested test coverage: schema tests, evidence linkage tests.
- Complexity: S

## Epic G: Graph / Relationship Visualization

### G1 - Relationship registry page

- Description: Add a dedicated page for all relationship types in the project.
- Why it matters: traceability is easier to trust when every relationship type is inspectable in one place.
- Dependencies: existing trace data.
- Acceptance criteria: users can filter links, SysML relations, containments, and impacts.
- Suggested test coverage: API tests, UI snapshot tests.
- Complexity: M

### G2 - Logical vs physical toggle

- Description: Add a toggle between logical architecture and physical realization views.
- Why it matters: the drone demo needs a simple way to show cross-domain traceability.
- Dependencies: D1.
- Acceptance criteria: the same project can be viewed through logical and physical representations.
- Suggested test coverage: UI state tests, seed rendering tests.
- Complexity: S

### G3 - Change impact visualization

- Description: Visualize the set of objects affected by a change request or requirement update.
- Why it matters: impact value is easier to communicate when it is visual.
- Dependencies: D4, E2.
- Acceptance criteria: impacted objects show type, version, and status in a readable visualization.
- Suggested test coverage: data mapping tests, UI snapshot tests.
- Complexity: M

Status:
Implemented as compact impact maps on requirement and change request detail pages.

## Epic H: Hardening, Tests, Docs

### H1 - Domain service split

- Description: Split the large service layer into smaller domain modules after the new entities land.
- Why it matters: the current service file works, but it will become hard to maintain as the model grows.
- Dependencies: C1, E1, F1.
- Acceptance criteria: domain services are separated without changing behavior.
- Suggested test coverage: existing API regression tests, import smoke tests.
- Complexity: L

Status:
Implemented with dedicated domain service entry points for impact and seed workflows while preserving the existing facade.

### H2 - Expanded backend coverage

- Description: Add tests for configuration, evidence, non-conformity, and connector behavior.
- Why it matters: the architecture will evolve quickly and needs regression coverage.
- Dependencies: the related feature epics.
- Acceptance criteria: every new domain capability has service or API tests.
- Suggested test coverage: model tests, service tests, API tests, export tests.
- Complexity: M

Status:
Implemented with a focused integration test covering configuration, connector, evidence, non-conformity, and export behavior.

### H3 - Aerospace demo narrative refresh

Status:
Implemented with refreshed seed copy and docs that make the demo read as mission need -> architecture -> evidence -> change.

- Description: Update seed data and copy so the drone scenario reads as mission need -> architecture -> evidence -> change.
- Why it matters: the demo should communicate connective tissue value immediately.
- Dependencies: D1, C1, E1.
- Acceptance criteria: the workspace clearly shows the new aerospace story.
- Suggested test coverage: seed checks, UI snapshot tests, export content checks.
- Complexity: S

## Recommended Phases

### Phase 1: Architecture-safe foundation

- B1
- B2
- C1
- C2
- E1

### Phase 2: Demo-visible aerospace differentiators

- B3
- C3
- C4
- D1
- D2
- E2
- E3
- H3

### Phase 3: Standards and connectors

- F1
- F2
- F3
- F4

### Phase 4: Advanced extensions

- D3
- D4
- G1
- G2
- G3
- H1
- H2

## Suggested Implementation Order

1. Harden frozen configuration contexts and add comparison.
2. Add first-class verification evidence and status derivation.
3. Add non-conformity and expand change lifecycle.
4. Add simulation and operational evidence variants.
5. Refresh the aerospace demo narrative around the new evidence and configuration model.
6. Add connector import contracts and standards mappings.
7. Add graph visualization and graph-aware traversal.
8. Split the service layer and expand test coverage.
