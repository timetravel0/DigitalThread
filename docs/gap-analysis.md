# Gap Analysis

## Executive Summary

ThreadLite now has a credible federation foundation. The current codebase implements project-scoped connector definitions, external authoritative artifacts, versioned external artifact records, artifact links, configuration contexts, and configuration item mappings. The drone demo seeds these objects, the API exposes them, the UI surfaces them, and the export bundle carries them forward.

That means the product is no longer just an internal authoring workspace. It has started to behave like connective tissue across engineering domains.

What it still is not: a full aerospace Digital Thread MVP. The next gaps are not about “having federation”; they are about making federation operationally useful. The current system still needs stronger configuration semantics, evidence-driven verification, non-conformity handling, richer realization modeling, standards-aware exchange contracts, and better relationship visualization. In other words, Epic A is the base layer. The remaining work is to make that base credible for review gates, closed-loop verification, and cross-domain change management.

The most important risk in the current foundation is governance hardness. Configuration contexts exist, but frozen contexts are not yet enforced as immutable review gates. That is a critical hardening concern because the next phases depend on stable configuration selection.

## Capability Matrix

| Requirement Area | Specific Capability | Current Status | Evidence in Code | Gap Description | Recommended Next Action |
|---|---|---:|---|---|---|
| AST / authoritative metadata federation | Project-scoped connector registry | Implemented | `ConnectorDefinition` model, `/api/projects/{project_id}/connectors`, registry UI | Foundation exists and is usable | Keep stable and use it as the source for later import/export adapters |
| AST / authoritative metadata federation | External authoritative artifact registry | Implemented | `ExternalArtifact` model, project list/detail endpoints, artifact registry UI | Metadata pointers are now first-class | Preserve metadata-only behavior and extend only with import contracts later |
| AST / authoritative metadata federation | External artifact version tracking | Implemented | `ExternalArtifactVersion`, version endpoints, seeded version history | Version pointers exist, but not yet selected by broader lifecycle logic | Use version records as the anchor for configuration contexts and verification evidence |
| AST / authoritative metadata federation | Artifact links to internal objects | Implemented | `ArtifactLink`, internal detail surfaces, link create/list/delete endpoints | The federation bridge is present | Keep link semantics stable and reuse them in future evidence and impact views |
| Configuration management / global configuration | Configuration contexts spanning internal and external versions | Implemented | `ConfigurationContext`, `ConfigurationItemMapping`, context detail and resolved view | A cross-domain context concept now exists | Build comparison, freeze semantics, and review-gate behavior on top of it |
| Configuration management / global configuration | Frozen review gate immutability | Risky | `ConfigurationContext.status` exists, but service/UI still allow edits and mapping changes | Frozen contexts can still be mutated, which weakens review-gate trust | Enforce immutability for frozen/released contexts before adding richer configuration features |
| Configuration management / global configuration | Context comparison and diffing | Missing | No context-to-context compare endpoint or UI | Users cannot answer what changed between gates | Add a comparison endpoint and a UI diff view in Epic B |
| Bidirectional traceability | Internal-to-external trace bridge | Implemented | Requirement/block/test pages surface linked external artifacts | Users can see the bridge directly from key lifecycle objects | Keep surfacing external links everywhere the object is edited or reviewed |
| Bidirectional traceability | Bidirectional traversal across lifecycle objects | Partial | Existing internal traceability remains in `Link` and `SysMLRelation`; artifact links add external edges | The model is richer, but not yet unified into one traversal strategy | Normalize traversal semantics in later traceability and graph work |
| MBSE / SysML alignment | Internal SysML-inspired trace semantics | Partial | Existing `SysMLRelation`, satisfaction, verification, derivation views | The internal model is useful but still not a standards-shaped contract | Preserve the current views and add mapping contracts rather than a rewrite |
| MBSE / SysML alignment | SysML v2-aligned mapping surface | Missing | No explicit mapping layer from current objects to SysML v2 concepts | Interoperability is still narrative rather than contract-based | Add an internal mapping contract in the standards/connectors phase |
| PLM / physical part linkage | Explicit physical part modeling | Partial | Generic `Component` and `Block` records, plus external PLM-linked artifacts | The demo can reference PLM parts, but physical realization is still partly generic | Keep the current abstraction for now and introduce a stronger part model only if needed |
| Software module traceability | Software realization traceability | Partial | Software appears through generic block/component typing and external links | No distinct software module lifecycle yet | Add a software realization layer only when the demo needs it |
| Test and verification evidence | Test execution records | Partial | `TestCase`, `TestRun`, test UI and demo data | Execution exists, but evidence is still run-centric | Build a dedicated evidence model in the next phase |
| Test and verification evidence | First-class verification evidence | Missing | No evidence domain object yet | Verification status cannot be derived from a durable evidence layer | Add verification evidence as a separate entity before expanding analytics |
| Simulation feedback | Simulation-linked evidence | Partial | Simulation appears as a test method or external artifact type | Simulation is not yet a distinct feedback loop | Introduce simulation evidence objects and rule-based status derivation |
| Operational telemetry feedback | Operational evidence ingestion | Partial | `OperationalRun` and telemetry JSON exist | Operational data is stored, but not yet used as evidence in a closed loop | Add a batch-oriented telemetry evidence object and summary rules |
| Impact analysis | Dependency-aware impact summaries | Partial | Existing impact analysis and change summaries remain useful | Current impact logic is still narrower than the future cross-domain model | Extend impact traversal after evidence and configuration semantics are stable |
| Review / approval workflow | Approval workflow for authored objects | Implemented | Existing workflow endpoints and approval actions remain in place | The core authored-object workflow is already solid | Keep as-is and extend auditability to change and non-conformity objects later |
| Review / approval workflow | Approval audit across federation and configuration changes | Partial | Approval logging exists for authored objects | Federation/configuration decisions are not yet covered in the same depth | Reuse the audit pattern in the next change and configuration phases |
| Non-conformities | First-class non-conformity object | Missing | No NCR model or UI exists | Issues are still implied by change requests | Add non-conformities as a separate lifecycle object |
| Change management | Full traceable change lifecycle | Partial | Change requests and impacts already exist | Lifecycle is present, but not yet tied to evidence, dispositions, and closure rules | Expand change management after evidence and non-conformity are in place |
| Baseline / review gates | Approved snapshot capture | Implemented | Baseline workflow remains intact | Baselines are still the authoritative internal snapshot mechanism | Keep baselines and distinguish them clearly from broader configuration contexts |
| Baseline / review gates | Gate comparison and freeze semantics | Partial | Baselines are captured, but comparison and stronger gate semantics are thin | Review gates need a more practical comparison workflow | Add baseline/context comparison and immutability rules in Epic B |
| Interoperability / APIs | API-first integration surface | Implemented | FastAPI routes and frontend client remain the primary contract | The product is already API-first | Preserve this and add new domain surfaces through the same pattern |
| Interoperability / APIs | Import/export exchange path | Partial | Export bundle includes federation data | Exchange is still mostly outbound | Add lightweight import contracts when connector work begins |
| Standards support | SysML v2-shaped mapping path | Missing | No mapping contract yet | Standards alignment is still conceptual | Introduce contract mapping after the configuration/evidence core is stable |
| Standards support | STEP AP242 and FMI placeholder contracts | Missing | No exchange contract surfaces for either standard | The current product does not yet demonstrate standards-aware interoperability | Add placeholder contracts, not full parsers, in the connector phase |
| Graph visualization | Relationship graph view | Missing | Current UI uses lists, cards, and matrices | Federation is visible, but not graph-centric | Add a node-link or relationship browser view after the core model settles |
| Export / exchange | Deterministic bundle with federation data | Implemented | Export now includes connectors, external artifacts, versions, links, contexts, and mappings | The bundle is useful as a handoff artifact | Keep the schema stable and use it as the seed for exchange contracts |
| Extensibility toward SME productization | Domain-specific architecture that can absorb more aerospace semantics | Partial | Monorepo, service layer, seeded drone demo, and clean federation primitives | The product is extensible, but some semantics are still generic | Evolve the next layers without disrupting the current federation base |

## Critical Gaps

1. Frozen configuration contexts are not yet enforced as immutable review gates.
2. There is no context-to-context comparison or configuration diff view.
3. Verification evidence is still run-centric rather than first-class and reusable.
4. Non-conformities are not modeled as independent lifecycle objects.
5. Standards-aware contracts for SysML v2, STEP AP242, and FMI are still missing.
6. Relationship visualization is still list-based rather than graph-based.
7. Change management is not yet tied to evidence, disposition, and closure semantics.
8. The physical part and software realization model is still partially generic.

## Recommended Implementation Sequence

1. Harden configuration contexts so frozen review gates are immutable and comparable.
2. Add configuration diffing and review-gate comparison.
3. Add first-class verification evidence and rule-based requirement status derivation.
4. Add non-conformity objects and connect them to evidence and change.
5. Expand change management into a traceable lifecycle with audit records.
6. Add lightweight standards contracts and import adapters.
7. Add graph-based trace visualization and traversal improvements.
8. Refine physical/software realization modeling only where the demo needs it.

