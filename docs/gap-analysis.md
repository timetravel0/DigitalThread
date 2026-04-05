# Gap Analysis

## Executive Summary

ThreadLite now has a credible federation foundation. The current codebase implements project-scoped connector definitions, external authoritative artifacts, versioned external artifact records, artifact links, configuration contexts, configuration item mappings, and a revision snapshot integrity summary for the internal AST history. The drone demo seeds these objects, the API exposes them, the UI surfaces them, and the export bundle carries them forward.

That means the product is no longer just an internal authoring workspace. It has started to behave like connective tissue across engineering domains.

What it still is not: a full aerospace Digital Thread MVP. The next gaps are not about “having federation”; they are about making federation operationally useful. The current system still needs stronger configuration semantics, evidence-driven verification, non-conformity handling, richer realization modeling, standards-aware exchange contracts, and better relationship visualization. In other words, Epic A is the base layer. The remaining work is to make that base credible for review gates, closed-loop verification, and cross-domain change management.

The most important remaining trust gap is cryptographic hardening. Configuration contexts are now enforced as immutable review gates, and the next step is to keep the AST history tamper-evident without turning the platform into a heavy event-sourcing system.

## Capability Matrix

| Requirement Area | Specific Capability | Current Status | Evidence in Code | Gap Description | Recommended Next Action |
|---|---|---:|---|---|---|
| AST / authoritative metadata federation | Project-scoped connector registry | Implemented | `ConnectorDefinition` model, `/api/projects/{project_id}/connectors`, registry UI | Foundation exists and is usable | Keep stable and use it as the source for later import/export adapters |
| AST / authoritative metadata federation | External authoritative artifact registry | Implemented | `ExternalArtifact` model, project list/detail endpoints, artifact registry UI | Metadata pointers are now first-class | Preserve metadata-only behavior and extend only with import contracts later |
| AST / authoritative metadata federation | External artifact version tracking | Implemented | `ExternalArtifactVersion`, version endpoints, seeded version history | Version pointers exist, but not yet selected by broader lifecycle logic | Use version records as the anchor for configuration contexts and verification evidence |
| AST / authoritative metadata federation | Artifact links to internal objects | Implemented | `ArtifactLink`, internal detail surfaces, link create/list/delete endpoints | The federation bridge is present | Keep link semantics stable and reuse them in future evidence and impact views |
| AST / authoritative metadata federation | Revision snapshot integrity summary | Implemented | `RevisionSnapshot` hash chain, authoritative registry integrity summary, registry UI | The internal history chain is now visible and checkable | Keep the summary additive and extend only if stronger signatures are needed later |
| Configuration management / global configuration | Configuration contexts spanning internal and external versions | Implemented | `ConfigurationContext`, `ConfigurationItemMapping`, context detail and resolved view | A cross-domain context concept now exists | Build comparison, freeze semantics, and review-gate behavior on top of it |
| Configuration management / global configuration | Frozen review gate immutability | Implemented | `ConfigurationContext.status`, service immutability checks, and UI guards now reject edits and mapping changes for frozen/released/obsolete contexts | Review gates are now protected from silent mutation | Preserve the current guard and extend only if stronger gate semantics are needed |
| Configuration management / global configuration | Context comparison and diffing | Missing | No context-to-context compare endpoint or UI | Users cannot answer what changed between gates | Add a comparison endpoint and a UI diff view in Epic B |
| Bidirectional traceability | Internal-to-external trace bridge | Implemented | Requirement/block/test pages surface linked external artifacts | Users can see the bridge directly from key lifecycle objects | Keep surfacing external links everywhere the object is edited or reviewed |
| Bidirectional traceability | Bidirectional traversal across lifecycle objects | Partial | Existing internal traceability remains in `Link` and `SysMLRelation`; artifact links add external edges | The model is richer, but not yet unified into one traversal strategy | Normalize traversal semantics in later traceability and graph work |
| MBSE / SysML alignment | Internal SysML-inspired trace semantics | Partial | Existing `SysMLRelation`, satisfaction, verification, derivation views | The internal model is useful but still not a standards-shaped contract | Preserve the current views and add mapping contracts rather than a rewrite |
| MBSE / SysML alignment | SysML v2-aligned mapping surface | Implemented | `SysMLMappingContractResponse`, `/api/projects/{project_id}/sysml/mapping-contract`, and the SysML mapping contract view | The internal model now has an explicit contract-shaped projection to SysML concepts | Preserve the mapping contract and extend it only when more standards contracts are needed |
| PLM / physical part linkage | Explicit physical part modeling | Partial | Generic `Component` and `Block` records, plus external PLM-linked artifacts | The demo can reference PLM parts, but physical realization is still partly generic | Keep the current abstraction for now and introduce a stronger part model only if needed |
| Software module traceability | Software realization traceability | Implemented | Dedicated `Software` workspace section, `software_module` component type, repository metadata in component detail, and evidence/traceability surfaces | Software realization is now explicit instead of implied | Preserve the current surface and extend it only if a dedicated lifecycle becomes necessary |
| Test and verification evidence | Test execution records | Partial | `TestCase`, `TestRun`, test UI and demo data | Execution exists, but evidence is still run-centric | Keep test runs as execution records and use evidence for reviewable claims |
| Test and verification evidence | First-class verification evidence | Implemented | `VerificationEvidence` model, requirement status engine, requirement detail UI, dashboard summary, and export bundle | Verification status can now be derived from a durable evidence layer | Preserve the current evidence model and extend it with future telemetry and simulation contracts only |
| Simulation feedback | Simulation-linked evidence | Implemented | `SimulationEvidence` is a first-class record with requirement, test case, and verification-evidence links | Simulation evidence is now distinct from test runs and generic verification evidence | Keep simulation evidence explicit and extend it with future contracts when needed |
| Operational telemetry feedback | Operational evidence ingestion | Implemented | `OperationalEvidence` model, requirement and verification evidence links, export bundle, and UI surfaces | Operational data is now stored as reviewable evidence batches | Preserve the current batch model and extend it only with future telemetry contracts |
| Impact analysis | Dependency-aware impact summaries | Implemented | Graph-aware impact traversal now crosses requirements, realization objects, tests, evidence, baselines, change requests, and external artifacts | The impact view is still intentionally compact, but the traversal now spans the broader model | Preserve the current traversal and extend only if future domains add new node types |
| Review / approval workflow | Approval workflow for authored objects | Implemented | Existing workflow endpoints and approval actions remain in place | The core authored-object workflow is already solid | Keep as-is and extend auditability to change and non-conformity objects later |
| Review / approval workflow | Approval audit across federation and configuration changes | Implemented | Approval logging now covers authored objects, baselines, configuration contexts, change requests, and non-conformities | The decision trail is visible across the main decision objects | Keep the current lightweight audit history and extend only if stronger governance is needed |
| Non-conformities | First-class non-conformity object | Implemented | NCR model, detail page, disposition workflow, and evidence links | Issues are now tracked as their own object | Extend the lifecycle rules and decision audit later if needed |
| Change management | Full traceable change lifecycle | Implemented | Change requests now retain analysis, disposition, implementation, closure notes, impacts, and audit history | The lifecycle is now visible and traceable, while still staying lightweight | Preserve the current lifecycle records and extend only if stronger governance is needed |
| Baseline / review gates | Approved snapshot capture | Implemented | Baseline workflow remains intact | Baselines are still the authoritative internal snapshot mechanism | Keep baselines and distinguish them clearly from broader configuration contexts |
| Baseline / review gates | Gate comparison and freeze semantics | Partial | Baselines are captured, but comparison and stronger gate semantics are thin | Review gates need a more practical comparison workflow | Add baseline/context comparison and immutability rules in Epic B |
| Interoperability / APIs | API-first integration surface | Implemented | FastAPI routes and frontend client remain the primary contract | The product is already API-first | Preserve this and add new domain surfaces through the same pattern |
| Interoperability / APIs | Import/export exchange path | Implemented | Export bundle includes federation data and the project import endpoint can create external artifacts and verification evidence from JSON or CSV | Exchange now includes a lightweight inbound path | Keep the importer small and extend it with connector-aware adapters later |
| Standards support | SysML v2-shaped mapping path | Implemented | SysML mapping contract endpoint, export bundle inclusion, and SysML mapping contract UI | SysML alignment is now explicit rather than narrative | Extend the contract only when newer standards mappings are required |
| Standards support | STEP AP242 placeholder contract | Implemented | `STEPAP242ContractResponse`, `/api/projects/{project_id}/step-ap242-contract`, export bundle inclusion, and the STEP AP242 contract view | Physical part linkage now has an explicit AP242-style contract shape | Keep the contract lightweight and focus FMI work only on future adapter needs |
| Standards support | FMI placeholder contract | Implemented | `FMIContractResponse`, `/api/projects/{project_id}/fmi-contracts`, export bundle inclusion, and the FMI contract view | Simulation interoperability now has an explicit placeholder contract shape | Keep the contract lightweight and extend it only when FMI-like adapters are needed |
| Graph visualization | Relationship graph view | Implemented | Compact graph explorer with walk-the-thread focus, CAD parts, software nodes, and evidence links | The graph is now available, but future densification or alternative layouts may still be useful | Preserve the current graph and extend only if a denser graph-native experience becomes necessary |
| Export / exchange | Deterministic bundle with federation data | Implemented | Export now includes connectors, external artifacts, versions, links, contexts, and mappings | The bundle is useful as a handoff artifact | Keep the schema stable and use it as the seed for exchange contracts |
| Extensibility toward SME productization | Domain-specific architecture that can absorb more aerospace semantics | Partial | Monorepo, service layer, seeded drone demo, and clean federation primitives | The product is extensible, but some semantics are still generic | Evolve the next layers without disrupting the current federation base |

## Critical Gaps

1. A cryptographic signature / Zero Trust trust model is still not implemented for the full AST history.
2. There is no context-to-context comparison or configuration diff view.
3. Non-conformities are modeled as independent lifecycle objects, but their lifecycle can still be hardened further if the product requires stricter audit rules.
4. Standards-aware contracts for FMI are implemented as a lightweight placeholder surface.
5. Relationship visualization now exists as a graph, but alternative layouts may still be useful for very dense projects.
6. Change management now carries traceable lifecycle semantics, but can still be hardened further if the governance model grows.
7. The physical part model remains partially generic, but software realization is now explicit.

## Recommended Implementation Sequence

1. Harden configuration contexts so frozen review gates are immutable and comparable.
2. Add configuration diffing and review-gate comparison.
3. Add non-conformity objects and connect them to evidence and change.
4. Expand change management only if a stricter governance model is required later.
5. Add FMI adapters and other lightweight import adapters.
6. Extend graph-based trace visualization only if denser relationship browsing becomes a future need.
7. Refine physical realization modeling only where the demo needs it.
