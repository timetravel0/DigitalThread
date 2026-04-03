# Target Architecture

## Product Positioning

ThreadLite v2 should be positioned as a connective metadata and traceability layer, not a replacement for PLM, MBSE, CAD, simulation, test, or telemetry tools.

The current federation foundation already proves the intended direction: ThreadLite registers authoritative external artifacts, stores version pointers, links internal authored objects to those sources, and groups selected versions into configuration contexts. The next architecture layers should build on that foundation instead of redefining it.

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

### Next Required Entities

#### VerificationEvidence

- Purpose: represent reusable verification claims and supporting evidence.
- Key fields: `id`, `project_id`, `evidence_type`, `title`, `status`, `source_type`, `source_reference`, `observed_at`, `expected_outcome`, `actual_outcome`, `metadata_json`.
- Relations: linked to requirements, tests, simulation records, telemetry batches, and non-conformities.
- Why needed: test runs alone are not enough to drive closed-loop verification.
- Phase: mandatory next.

#### SimulationEvidence

- Purpose: represent simulation scenarios and outcomes separately from generic test execution.
- Key fields: `id`, `project_id`, `model_reference`, `scenario_name`, `inputs_json`, `expected_behavior_json`, `observed_behavior_json`, `result`, `run_at`.
- Relations: linked to requirements and verification evidence.
- Why needed: simulation feedback should be queryable and comparable on its own terms.
- Phase: mandatory next if simulation is part of the demo story.

#### OperationalEvidence

- Purpose: represent batches of field or operational telemetry used as verification input.
- Key fields: `id`, `project_id`, `source_name`, `captured_at`, `coverage_window`, `telemetry_json`, `quality_status`, `derived_metrics_json`.
- Relations: linked to requirements and verification evidence.
- Why needed: enables a practical digital-twin style feedback loop without a streaming platform.
- Phase: mandatory for a credible closed-loop story.

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
- Phase: optional until the demo needs it.

#### PhysicalPart

- Purpose: model a real PLM part explicitly when `Component` is too generic.
- Key fields: `id`, `project_id`, `part_number`, `name`, `supplier`, `revision`, `status`, `lifecycle_state`, `external_artifact_id`.
- Relations: linked to logical blocks, software modules, and external artifact versions.
- Why needed: a physical realization model makes PLM linkage easier to explain.
- Phase: optional if existing `Component` semantics remain sufficient.

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

- Start with fake, JSON, and CSV adapters.
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
- non-conformity pages,
- graph or relationship visualization,
- logical vs physical traceability views,
- standards and connector contract pages,
- evidence-driven impact summaries.

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

