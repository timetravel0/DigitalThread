# Ralph Fix Plan

## Stories to Implement

### Global Configuration & Baselines
> Goal: Goal: Make review gates and configuration selection first-class so users can compare approved states across internal and external objects.

- [x] Story 2.1: Configuration Context Comparison
- [x] Story 2.2: Frozen Context Immutability
- [x] Story 2.3: Baseline To Context Bridge
### Verification Evidence & Closed Loop
> Goal: Goal: Make verification status evidence-driven instead of relying only on authored approval state.

- [x] Story 3.1: Verification Evidence Model
- [x] Story 3.2: Requirement Verification Status Engine
- [x] Story 3.3: Simulation Evidence Records
- [x] Story 3.4: Operational Evidence Batches
### Aerospace Traceability Enrichment
> Goal: Goal: Make the drone demo read like a real aerospace thread from mission need to realization and evidence.

- [x] Story 4.1: Logical Vs Physical View Cues
- [x] Story 4.2: Software Realization Traceability
- [x] Story 4.3: Traceability Graph View
- [x] Story 4.4: Graph-Aware Impact Traversal
### Non-Conformity & Change
> Goal: Goal: Separate issue disposition from generic change tracking and make closure traceable.

- [x] Story 5.1: Non-Conformity Entity
- [x] Story 5.2: Change Lifecycle Expansion
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
