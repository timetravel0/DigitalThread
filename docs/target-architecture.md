# Target Architecture

## Product Positioning

ThreadLite v2 should be positioned as a connective metadata and traceability layer, not a replacement for PLM, MBSE, CAD, simulation, test, or telemetry tools.

The current federation foundation already proves the intended direction: ThreadLite registers authoritative external artifacts, stores version pointers, links internal authored objects to those sources, groups selected versions into configuration contexts, and now exposes a revision snapshot integrity summary for the internal AST history. The next architecture layers should build on that foundation instead of redefining it.

Several of the later domain contracts described below are already implemented in the current codebase. This document remains a reference architecture for the remaining extension path and for the semantics we want to preserve as the product grows.

## Architecture Principles

1. Metadata federation over file duplication.
2. External artifact pointers instead of copied source files.
3. Project context plus configuration context for every meaningful relationship.
4. Explicit, typed traceability semantics.
5. Verification evidence as a first-class object.
6. Approved baselines and review gates must remain frozen and comparable.
7. Connectors should stay modular and lightweight before becoming real integrations.
8. API-first design should remain the primary integration path.
9. Standards-aware modeling should be practical and contract-driven.
10. The AST history should be tamper-evident without becoming heavy event sourcing.

## Existing Foundation

Epic A is already present and should be treated as the base layer:

- `ConnectorDefinition`
- `ExternalArtifact`
- `ExternalArtifactVersion`
- `ArtifactLink`
- `ConfigurationContext`
- `ConfigurationItemMapping`

That foundation gives the product a usable federation registry, a version pointer model, and a configuration scope. The target architecture should expand from there.

## Domain Model Evolution

### Core Foundation Already In Place

- `ConnectorDefinition`: project-scoped registry entry for an external source/tool.
- `ExternalArtifact`: metadata-only reference to an authoritative external object.
- `ExternalArtifactVersion`: version or revision record for an external artifact.
- `ArtifactLink`: bridge between internal authored objects and external authoritative sources.
- `ConfigurationContext`: project-scoped cross-domain configuration snapshot.
- `ConfigurationItemMapping`: selection record for internal or external versions in a context.

### Evidence and Domain Extensions

The following entities are already implemented in the current codebase and form part of the current foundation:

- `VerificationEvidence`
- `SimulationEvidence`
- `OperationalEvidence`

The architecture below still describes the intended semantics and extension path for these objects and the remaining related entities.

#### VerificationEvidence

- Purpose: represent reusable verification claims and supporting evidence.
- Key fields: `id`, `project_id`, `evidence_type`, `title`, `status`, `source_type`, `source_reference`, `observed_at`, `expected_outcome`, `actual_outcome`, `metadata_json`.
- Relations: linked to requirements, tests, simulation records, telemetry batches, and non-conformities.
- Why needed: test runs alone are not enough to drive closed-loop verification.
- Phase: implemented.

#### SimulationEvidence

- Purpose: represent simulation scenarios and outcomes separately from generic test execution.
- Key fields: `id`, `project_id`, `model_reference`, `scenario_name`, `inputs_json`, `expected_behavior_json`, `observed_behavior_json`, `result`, `run_at`.
- Relations: linked to requirements and verification evidence.
- Why needed: simulation feedback should be queryable and comparable on its own terms.
- Phase: implemented.

#### OperationalEvidence

- Purpose: represent batches of field or operational telemetry used as verification input.
- Key fields: `id`, `project_id`, `source_name`, `captured_at`, `coverage_window`, `telemetry_json`, `quality_status`, `derived_metrics_json`.
- Relations: linked to requirements and verification evidence.
- Why needed: enables a practical digital-twin style feedback loop without a streaming platform.
- Phase: implemented.

#### NonConformity

- Purpose: manage non-conformities as first-class engineering objects.
- Key fields: `id`, `project_id`, `key`, `title`, `description`, `severity`, `status`, `detected_at`, `root_cause`, `disposition`, `closure_notes`.
- Relations: linked to evidence, impacted objects, change requests, and approval records.
- Why needed: aerospace issue management is not the same as generic change tracking.
- Phase: mandatory.

#### ApprovalRecord

- Purpose: create a stable audit trail for decisions across workflow objects.
- Key fields: `id`, `project_id`, `object_type`, `object_id`, `action`, `from_status`, `to_status`, `actor`, `decision_at`, `comment`, `context_id`.
- Relations: attaches to requirements, changes, baselines, contexts, and non-conformities.
- Why needed: strengthens traceability without replacing existing workflow mechanics.
- Phase: can extend the current approval log pattern.

#### SoftwareModule

- Purpose: model software realization explicitly when the generic component/block split is not precise enough.
- Key fields: `id`, `project_id`, `name`, `key`, `version`, `repository_ref`, `status`, `metadata_json`.
- Relations: linked to requirements, blocks, external artifacts, and verification evidence.
- Why needed: flight software often needs a clearer lifecycle than a generic block.
- Phase: implemented as a dedicated software realization surface on top of the existing `Component` model with `type = software_module`.

#### PhysicalPart

- Purpose: model a real PLM part explicitly when `Component` is too generic.
- Key fields: `id`, `project_id`, `part_number`, `name`, `supplier`, `revision`, `status`, `lifecycle_state`, `external_artifact_id`.
- Relations: linked to logical blocks, software modules, and external artifact versions.
- Why needed: a physical realization model makes PLM linkage easier to explain.
- Phase: optional if existing `Component` semantics remain sufficient.

#### SysMLMappingContract

- Purpose: expose the current internal model as a contract-shaped SysML v2-inspired mapping surface without replacing the native ThreadLite objects.
- Key fields: project, requirement mappings, block mappings, explicit satisfy/verify/deriveReqt/contain relations, and summary counts.
- Relations: derived from requirements, blocks, SysML relations, and block containments.
- Why needed: standards alignment should be explicit and exportable even before any native SysML v2 engine exists.
- Phase: implemented.

#### STEPAP242Contract

- Purpose: expose a lightweight AP242-style part contract from the current component and external-artifact model.
- Key fields: project, part rows, part numbers, identifiers, linked cad_part artifacts, and summary counts.
- Relations: derived from physical components, `cad_part` external artifacts, and artifact links.
- Why needed: physical part interoperability should be explicit without introducing a CAD integration layer.
- Phase: implemented.

#### FMIContract

- Purpose: expose a lightweight FMI-style model reference contract from the current simulation evidence and contract model.
- Key fields: project, model identifier, model version, model URI, adapter profile, linked simulation evidence, and summary counts.
- Relations: derived from simulation evidence, requirement links, and the FMI contract-shaped surface.
- Why needed: simulation interoperability should be explicit without introducing an FMI runtime or adapter engine.
- Phase: implemented.

## Traceability Model

The target drone thread should support chains like:

Mission Need
-> System Requirement
-> Derived Requirement
-> Logical Block
-> Physical Part
-> Software Module
-> Verification Artifact / Test
-> Simulation or Operational Evidence
-> Change Request / Non-Conformity

The key rule is bidirectionality. Users must be able to navigate from a mission need downward into realization and evidence, and also from a failed test or part change back up to the affected requirements and review gates.

## Configuration Model

`ConfigurationContext` should evolve into the practical global configuration for the MVP.

It should:

- define a review gate or working set explicitly,
- select internal object versions,
- select external artifact versions,
- remain project-scoped,
- compare against another context,
- and provide a stable scope for impact analysis and verification status.

This does not need to become an enterprise configuration engine. It only needs to answer: “What exact combination of internal and external definitions was approved at this gate?”

## Connector Model

The connector model should remain intentionally lightweight.

- JSON and CSV import adapters are already implemented as the first inbound contract.
- Keep future fake adapters lightweight when they are added.
- Store connector definitions as data, not code branches.
- Keep authoritative references as metadata only.
- Allow future REST integrations without changing the object model.
- Treat import/export contracts as first-class before real sync jobs.

This keeps the product honest about what it is: connective metadata infrastructure, not a replacement for the source systems.

## Verification Loop

The requirement verification state should be derived from linked evidence using a small rule model:

- `verified`
- `partially_verified`
- `at_risk`
- `failed`
- `not_covered`

Suggested evaluation order:

1. Prefer evidence in the active configuration context.
2. Consider explicit test, simulation, and operational evidence before inferred data.
3. Compare observed results to expected thresholds or design behavior.
4. Roll the result up to requirement and dashboard status.

Authoring approval status and verification status must remain separate.

## UI Architecture Evolution

The major UI additions after federation are:

- configuration comparison and review-gate views,
- verification evidence pages,
- a lightweight validation cockpit with dropdown-based checks,
- non-conformity pages,
- graph / relationship visualization for walk-the-thread exploration,
- logical vs physical traceability views,
- standards and connector contract pages,
  - evidence-driven impact summaries and compact impact maps.

The existing dashboard, project workspace, matrix, and detail pages should remain the backbone. New views should extend that backbone rather than replacing it.

## Migration Strategy

The next architecture phase should evolve incrementally:

- Keep the current federation tables and API contracts.
- Add evidence, non-conformity, and configuration comparison tables.
- Extend the existing workflow and audit pattern instead of introducing a separate approval system.
- Keep the current monorepo and service structure until the new domains justify splitting services.
- Introduce standards mappings and import contracts as lightweight adapters, not hard integrations.

What should remain as-is for now:

- the FastAPI + Next.js stack,
- the federation registry,
- the existing review workflow,
- the baseline snapshot mechanism,
- the matrix and impact surfaces,
- the seeded drone demo.

What should be refactored later:

- overly generic physical/software semantics,
- impact traversal logic,
- relationship traversal if it stays split across multiple edge types,
- export logic once exchange contracts become more formal.

## Risks and Trade-offs

Do not build a heavy graph database, a full enterprise PLM replacement, or a deeply generic workflow engine yet.

The near-term product should optimize for:

- clear aerospace narrative,
- configuration-aware traceability,
- verification credibility,
- practical connectors,
- and a defensible connective-layer position.

The product should stay lightweight, but the semantics need to become stricter. The architecture must become more precise, not just larger.
