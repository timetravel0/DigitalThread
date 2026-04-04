# Ralph Fix Plan

## Stories to Implement

### Global Configuration & Baselines
> Goal: Goal: Make review gates and configuration selection first-class so users can compare approved states across internal and external objects.

- [x] Story 2.1: Configuration Context Comparison
- [x] Story 2.2: Frozen Context Immutability
- [ ] Story 2.3: Baseline To Context Bridge
  > As an engineering lead
  > I want baselines and configuration contexts to be clearly related
  > So that I can explain the difference between a frozen internal snapshot and a broader review gate.
  > AC: Given a baseline, when I inspect it, then I can see the related configuration context if one exists.
  > AC: Given a configuration context, when it references a baseline, then the relationship is visible in the UI.
  > AC: Given the project workspace, when I navigate review artifacts, then baselines and contexts are clearly distinct.
  > Spec: specs/planning-artifacts/epics.md#story-2-3
### Verification Evidence & Closed Loop
> Goal: Goal: Make verification status evidence-driven instead of relying only on authored approval state.

- [ ] Story 3.1: Verification Evidence Model
  > As a verification engineer
  > I want first-class verification evidence records
  > So that I can reuse evidence across requirements, tests, simulation, and telemetry.
  > AC: Given evidence data, when I create a record, then it can be linked to a requirement or test.
  > AC: Given evidence records, when I view export data, then they are included.
  > AC: Given a requirement detail page, when evidence exists, then linked evidence is visible.
  > Spec: specs/planning-artifacts/epics.md#story-3-1
- [ ] Story 3.2: Requirement Verification Status Engine
  > As a product user
  > I want requirement verification status to be derived from evidence
  > So that the dashboard reflects engineering reality.
  > AC: Given linked evidence, when the rule engine evaluates a requirement, then it resolves to verified, partially_verified, at_risk, failed, or not_covered.
  > AC: Given no evidence, when evaluation runs, then the requirement is marked not_covered.
  > AC: Given stale or incomplete evidence, when evaluation runs, then the requirement is not marked verified.
  > Spec: specs/planning-artifacts/epics.md#story-3-2
- [ ] Story 3.3: Simulation Evidence Records
  > As a simulation engineer
  > I want simulation runs to be captured as evidence
  > So that model behavior can be compared against expected behavior.
  > AC: Given a simulation result, when I record it, then the model, scenario, inputs, and outputs are preserved.
  > AC: Given a simulation evidence record, when I view it, then it can be linked to requirements and exported.
  > AC: Given the seeded demo, when I open the simulation-related thread, then the simulation evidence is understandable.
  > Spec: specs/planning-artifacts/epics.md#story-3-3
- [ ] Story 3.4: Operational Evidence Batches
  > As an operations or flight-test user
  > I want telemetry batches to be captured as evidence
  > So that field feedback can update verification status.
  > AC: Given telemetry data, when I ingest a batch, then it is stored as operational evidence.
  > AC: Given an operational evidence batch, when I inspect it, then the relevant requirement or context is visible.
  > AC: Given evaluation rules, when telemetry changes, then requirement status can be updated.
  > Spec: specs/planning-artifacts/epics.md#story-3-4
### Aerospace Traceability Enrichment
> Goal: Goal: Make the drone demo read like a real aerospace thread from mission need to realization and evidence.

- [ ] Story 4.1: Logical Vs Physical View Cues
  > As a systems engineer
  > I want logical and physical artifacts to be visually distinguishable
  > So that I can understand the architecture split at a glance.
  > AC: Given the project workspace, when I inspect nodes, then logical and physical artifacts are visually distinct.
  > AC: Given the drone seed, when I view the thread, then the narrative separates architecture from realization.
  > AC: Given detail pages, when artifact type matters, then the UI explains it clearly.
  > Spec: specs/planning-artifacts/epics.md#story-4-1
- [ ] Story 4.2: Software Realization Traceability
  > As a software lead
  > I want software realization to be modeled explicitly
  > So that flight software can be traced alongside hardware and requirements.
  > AC: Given a software realization object, when I link it, then it can connect to requirements, blocks, and evidence.
  > AC: Given a software artifact, when I inspect its detail view, then traceability is visible.
  > AC: Given the export bundle, when I export the project, then software trace data is included if implemented.
  > Spec: specs/planning-artifacts/epics.md#story-4-2
- [ ] Story 4.3: Traceability Graph View
  > As a reviewer
  > I want a graph view of the thread
  > So that I can inspect relationships visually instead of only through lists.
  > AC: Given a node, when I expand it, then connected objects and relationship types are visible.
  > AC: Given the project graph, when I filter it, then I can focus on requirements, blocks, parts, tests, or evidence.
  > AC: Given no data, when the graph loads, then the empty state is usable.
  > Spec: specs/planning-artifacts/epics.md#story-4-3
- [ ] Story 4.4: Graph-Aware Impact Traversal
  > As an engineer reviewing change
  > I want impact analysis to follow the broader thread model
  > So that affected requirements, realization objects, tests, and evidence are visible.
  > AC: Given a changed object, when impact analysis runs, then the result includes downstream and upstream relations.
  > AC: Given a cycle or repeated relation, when traversal runs, then it does not loop forever.
  > AC: Given evidence and configuration context, when impact analysis runs, then the output respects the active context.
  > Spec: specs/planning-artifacts/epics.md#story-4-4
### Non-Conformity & Change
> Goal: Goal: Separate issue disposition from generic change tracking and make closure traceable.

- [ ] Story 5.1: Non-Conformity Entity
  > As a quality engineer
  > I want non-conformities to be first-class records
  > So that issue disposition is separated from ordinary change requests.
  > AC: Given a detected issue, when I create a non-conformity, then it has its own lifecycle state.
  > AC: Given a non-conformity, when I inspect it, then linked evidence and impacted objects are visible.
  > AC: Given export data, when I export the project, then non-conformities are included if implemented.
  > Spec: specs/planning-artifacts/epics.md#story-5-1
- [ ] Story 5.2: Change Lifecycle Expansion
  > As an approver
  > I want change requests to have a traceable lifecycle
  > So that analysis, approval, implementation, and closure are visible.
  > AC: Given an open change request, when it moves through states, then each transition is valid and traceable.
  > AC: Given a resolved change request, when I inspect it, then the closure path is visible.
  > AC: Given audit history, when a change is approved, then the transition is recorded.
  > Spec: specs/planning-artifacts/epics.md#story-5-2
- [ ] Story 5.3: Audit Reuse Across Decision Objects
  > As a compliance reviewer
  > I want audit records to be consistent across contexts, baselines, changes, and non-conformities
  > So that the decision trail is easy to trust.
  > AC: Given a decision event, when it occurs, then an audit record is written.
  > AC: Given a review gate or change object, when I inspect history, then actor and decision time are visible.
  > AC: Given a rejected action, when it is recorded, then the reason is captured.
  > Spec: specs/planning-artifacts/epics.md#story-5-3
### Connector Framework & Standards Contracts
> Goal: Goal: Add lightweight exchange contracts so the federation layer can ingest and describe external data without pretending to be a full integration platform.

- [ ] Story 6.1: JSON And CSV Importer
  > As an integration user
  > I want to import simple JSON or CSV exports
  > So that external metadata can populate the thread quickly.
  > AC: Given a JSON or CSV payload, when I import it, then external artifacts or versions can be created or updated.
  > AC: Given invalid input, when I import it, then the error is actionable.
  > AC: Given an import result, when I inspect it, then the affected objects are visible.
  > Spec: specs/planning-artifacts/epics.md#story-6-1
- [ ] Story 6.2: SysML V2 Mapping Contract
  > As an MBSE practitioner
  > I want the internal model to map to SysML v2-shaped concepts
  > So that the product can evolve toward standards-aware exchange.
  > AC: Given requirements and blocks, when I inspect the mapping, then satisfy, verify, and derive semantics are explicit.
  > AC: Given the current model, when I export the mapping contract, then the shape is stable and documented.
  > AC: Given future integrations, when they consume the mapping, then they do not need a rewrite of the core model.
  > Spec: specs/planning-artifacts/epics.md#story-6-2
- [ ] Story 6.3: STEP AP242 Placeholder Contract
  > As a PLM-oriented user
  > I want a placeholder AP242-style contract for part metadata
  > So that physical part linkage has a named exchange shape.
  > AC: Given a physical part reference, when I export it, then the metadata contract is recognizable as AP242-oriented.
  > AC: Given a part exchange payload, when I inspect it, then the contract is versioned and documented.
  > Spec: specs/planning-artifacts/epics.md#story-6-3
- [ ] Story 6.4: FMI Placeholder Contract
  > As a simulation-oriented user
  > I want a placeholder FMI-style contract for model metadata
  > So that simulation evidence can point at a standards-aware shape.
  > AC: Given simulation evidence, when I inspect the contract, then the model reference and version are explicit.
  > AC: Given future integration work, when an FMI adapter is added, then it can use the placeholder contract.
  > Spec: specs/planning-artifacts/epics.md#story-6-4
### Graph / Relationship Visualization
> Goal: Goal: Make relationship data easier to inspect and explain.

- [ ] Story 7.1: Relationship Registry Page
  > As a reviewer
  > I want a registry of relationships
  > So that I can inspect all relationship types in one place.
  > AC: Given the project, when I open the registry page, then links and trace relations are visible.
  > AC: Given filters, when I apply them, then I can focus on specific object types or relation types.
  > Spec: specs/planning-artifacts/epics.md#story-7-1
- [ ] Story 7.2: Logical Vs Physical Toggle
  > As a demo viewer
  > I want a logical vs physical toggle
  > So that I can understand the thread in the right architectural layer.
  > AC: Given the same project, when I switch modes, then the visible objects change to the selected layer.
  > AC: Given the drone demo, when the toggle is used, then the aerospace story becomes clearer.
  > Spec: specs/planning-artifacts/epics.md#story-7-2
- [ ] Story 7.3: Change Impact Visualization
  > As a manager
  > I want impact to be visual
  > So that I can understand risk quickly.
  > AC: Given a change or requirement update, when impact is calculated, then affected objects are shown visually.
  > AC: Given impacted objects, when I inspect them, then type, version, and status are visible.
  > Spec: specs/planning-artifacts/epics.md#story-7-3
### Hardening, Tests, Docs
> Goal: Goal: Keep the product stable as the model expands.

- [ ] Story 8.1: Domain Service Split
  > As a developer
  > I want the service layer split into domain modules
  > So that the codebase remains maintainable as the model grows.
  > AC: Given the current service layer, when the split is complete, then behavior remains unchanged.
  > AC: Given new domains, when they are added, then they do not require one giant service file.
  > Spec: specs/planning-artifacts/epics.md#story-8-1
- [ ] Story 8.2: Expanded Backend Coverage
  > As a maintainer
  > I want stronger automated coverage
  > So that the next epics do not break federation or baseline behavior.
  > AC: Given new configuration or evidence behavior, when tests run, then regressions are caught.
  > AC: Given export bundle changes, when tests run, then the schema remains stable.
  > Spec: specs/planning-artifacts/epics.md#story-8-2
- [ ] Story 8.3: Aerospace Demo Narrative Refresh
  > As a product reviewer
  > I want the drone demo to tell a clearer aerospace story
  > So that the value of the product is visible immediately.
  > AC: Given the drone seed, when I open the app, then the narrative reads as mission need -> architecture -> parts -> evidence -> change.
  > AC: Given the homepage and project workspace, when I inspect the demo, then federation is obvious.
  > Spec: specs/planning-artifacts/epics.md#story-8-3

## Completed

## Notes
- Follow TDD methodology (red-green-refactor)
- One story per Ralph loop iteration
- Update this file after completing each story
