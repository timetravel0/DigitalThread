# ThreadLite Platform Logic Guide

This guide explains how ThreadLite works internally.

## 1. Core Principle

ThreadLite is a project-centric engineering workspace.

The platform keeps six ideas separate:

- authored objects, such as requirements, blocks, and test cases
- execution records, such as test runs and operational runs
- reusable evidence, such as `VerificationEvidence`
- simulation evidence records, which capture model-based results as a first-class object
- FMI placeholder contracts, which capture model reference metadata for simulation interoperability
- operational evidence batches, which capture reviewable field or telemetry summaries
- configuration snapshots, such as baselines and configuration contexts

Keeping those concerns separate makes the platform easier to reason about and safer to extend.

## 2. Data Flow

The usual data flow is:

1. create a project
2. author requirements, blocks, test cases, components, and relations
3. submit selected authored objects for review
4. approve the objects that are ready
5. capture evidence, simulation evidence, operational evidence, test runs, operational runs, and change requests
6. freeze approved content in baselines or configuration contexts
7. export the project bundle for external validation

## 3. Authoring Logic

Requirements, blocks, and test cases support an approval lifecycle:

- `draft`
- `in_review`
- `approved`
- `rejected`
- `obsolete`

The important rules are:

- draft and rejected items can be edited directly
- approved items are immutable in place
- editing an approved item requires creating a new draft version
- obsolete items are treated as read-only

The UI follows the same rule set that the backend enforces.

## 4. Versioning Logic

ThreadLite uses pragmatic versioning:

- the live object carries a `version` field
- revision snapshots preserve previous versions and summaries
- each revision snapshot stores a content hash and previous-hash pointer so the history is harder to tamper with
- an approved object stays as the historical record for that version
- a new draft version is created when a changed approved item needs review

This is intentionally simpler than full event sourcing.

## 5. Traceability Logic

Traceability uses explicit relationships instead of inferred behavior.

Main relation families:

- generic links between project objects
- SysML-inspired relations such as `satisfy`, `verify`, `deriveReqt`, `trace`, `allocate`, and `contain`
- block containment for structural hierarchy
- external artifact links for federated metadata

Rules:

- cross-project relations are rejected
- relation types are validated by the service layer
- object existence is checked before a relation is created

The relationship registry is a read-only registry view built from the same underlying relationship data.

It groups:

- requirements
- generic traceability links
- SysML relations
- artifact links
- verification, simulation, and operational evidence

The registry does not invent new semantics.
It gives reviewers a filtered list view so they can inspect traceability without opening the graph or jumping between separate pages.

## 6. Verification Logic

Verification uses a layered model:

- `TestRun` records the execution of a test case
- `OperationalRun` records field or mission evidence
- `VerificationEvidence` stores reusable evidence objects that can point to requirements, tests, components, and later simulation or telemetry inputs
- `SimulationEvidence` stores simulation-specific records with model reference, scenario, inputs, expected behavior, observed behavior, result, and execution timestamp
- `OperationalEvidence` stores reviewable operational batches with source, time window, observations, and derived metrics
- requirement detail pages keep approval status separate from verification status
- the verification engine also exposes a plain-language decision source and summary for reviewers

Evaluation is evidence-led:

- explicit verification evidence signals take precedence
- compatible test runs and operational runs act as fallback when evidence is neutral
- failures dominate risk, and risk dominates partial support
- approval status stays separate from verification status

Why this matters:

- execution records answer "what happened"
- evidence answers "what can we reuse and review"
- simulation evidence answers "what did the model predict and what did the simulation actually show"
- operational evidence answers "what did the field batch tell us in a reviewable form"

The requirement verification status engine derives the current state from linked evidence and test results.

Operational evidence stays separate from operational runs so the platform can preserve both the raw execution record and the reviewable batch summary.

The dashboard and project summary pages use the computed verification states to show a small distribution across:

- `verified`
- `partially_verified`
- `at_risk`
- `failed`
- `not_covered`

## 7. Baseline Logic

Baselines are frozen internal snapshots.

When a baseline is created:

- only approved requirements, blocks, and test cases are included by default
- the object version is captured at baseline time
- baseline items keep object type, object id, and object version

This means a baseline answers:

- what was approved
- which version was approved

## 8. Configuration Context Logic

Configuration contexts are broader than baselines.

They can combine:

- internal object versions
- external artifact versions
- review-gate metadata

They support:

- comparison between contexts
- comparison between baselines
- a bridge from baseline to related configuration context
- immutability for frozen, released, and obsolete contexts

Use baselines when you want a frozen internal snapshot.
Use configuration contexts when you want a review gate or mixed internal/external scope.

## 9. Impact Logic

Impact analysis is pragmatic, not exhaustive graph theory.

The traversal uses:

- direct relations
- one extra hop
- readable summaries grouped by object type

The UI renders impact as a compact impact map:

- requirements show direct impacts, secondary impacts, related baselines, and open change requests
- change requests show impacted objects grouped by impact level
- the map is intentionally smaller than the traceability graph so reviewers can understand it quickly

When a requirement changes, the impact view looks at:

- linked blocks
- linked tests
- derived requirements
- baselines
- change requests

When a block changes, the impact view looks at:

- satisfied requirements
- linked tests
- parent and child blocks through containment
- downstream evidence and change records where relevant

## 10. Matrix Logic

The matrix view is a deterministic coverage table.

- rows = requirements
- columns = components or tests
- cell = whether a relation exists

This view is intentionally simple so reviewers can answer coverage questions quickly.

## 11. SysML-Inspired Semantics

ThreadLite implements a focused SysML subset:

- `Block` models a structural element
- `contain` expresses block hierarchy
- `satisfy` expresses block-to-requirement realization
- `verify` expresses test-to-requirement verification
- `deriveReqt` expresses requirement derivation
- `SysML mapping contract` exposes the current model as a contract-shaped SysML v2-inspired export surface
- `STEP AP242 placeholder contract` exposes the current part metadata and `cad_part` external artifacts as a contract-shaped AP242-style export surface
- `FMI placeholder contract` exposes the current model reference metadata as a contract-shaped FMI-style export surface

The platform does not implement the full SysML specification.
It implements just enough semantics to support practical aerospace authoring and review.

The logical vs physical toggle is implemented as a read-only projection over `Block.abstraction_level`:

- `logical` blocks represent architecture intent, subsystem decomposition, and design structure
- `physical` blocks represent realization-oriented structure and implementation-oriented parts
- `all` shows both layers together

This toggle does not change the underlying data model or create alternate records.

## 12. Seed Logic

The seeded drone project is intentionally structured to exercise the main platform rules:

- requirements cover endurance, video, environment, obstacle detection, and telemetry
- blocks show logical and physical structure
- components map realization
- tests provide verification
- simulation evidence, operational evidence, and runs show closed-loop behavior
- a change request and a baseline demonstrate review control

The demo narrative is deliberate: mission need -> architecture -> evidence -> change

- mission need drives the endurance requirement
- logical blocks describe architecture intent
- physical components and software realize the design
- test runs, simulation evidence, and operational evidence capture verification feedback
- the endurance shortfall drives a change request and impact records

The seed is designed to make the dashboard, matrix, graph, SysML, and export views useful immediately.

The traceability graph is intentionally a compact relationship explorer rather than a node-link canvas.

- the graph includes all objects that belong to the chosen focus
- the focus buttons reduce the network only when the reviewer wants less density
- clicking a box opens a focused graph with separate Incoming / Focus / Outgoing columns
- the default view is compact and card-based, while the focused view uses a wider graph layout with visible link labels, visible edge ports on the box boundary, separators, and extra routing space for repeated links between the same objects
- relation explanations sit on the link itself so reviewers can see why the relation exists

## 13. Export Logic

The export bundle is a deterministic JSON package.

It includes:

- project metadata
- authored objects
- execution records
- evidence
- simulation evidence and simulation evidence links
- operational evidence and operational evidence links
- imported external artifacts and verification evidence
- traceability relations
- baselines and change records
- revision snapshots
- configuration context data

Why this matters:

- external tools can validate the result without needing the UI
- the bundle can serve as an audit or handoff artifact

## 14. Import Logic

Import is intentionally lightweight.

The API accepts JSON or CSV text and maps rows into:

- `ExternalArtifact`
- `VerificationEvidence`

Rules:

- each record must declare or imply a record type
- imported verification evidence must link to at least one requirement, test case, component, or non-conformity
- non-conformities can carry an explicit deviation disposition (`accept`, `rework`, or `reject`) without replacing their lifecycle status
- imported rows stay inside the selected project
- the import workflow does not create a separate job table yet

Why this matters:

- it gives the demo a practical external ingestion path
- it keeps the importer simple enough to review in the UI
- it avoids adding a larger file pipeline before the product needs it

## 15. Local Runtime Logic

ThreadLite supports two runtime modes:

- Docker Compose with PostgreSQL
- direct local execution with SQLite

The local mode is intentionally simple so developers can work without a database server.

## 16. Documentation Logic

The repository documentation is surfaced inside the application as a built-in manual.

That means:

- the UI reads the markdown files stored in the repository
- the docs section is part of the application, not a separate site
- the user guide should remain aligned with the actual screens and flows
- the platform logic guide should remain aligned with the backend rules

## 17. Service Layer Structure

The backend service layer is split into a small set of domain entry points for maintainability.

- the legacy `app.services` facade still exists for compatibility
- impact-oriented routes use a dedicated impact service module
- demo seeding uses a dedicated seed service module

This split keeps the behavior stable while making the high-change domains easier to locate.

## 18. What Is Intentionally Deferred

The platform does not yet implement:

- a full SysML editor
- a full status engine for all evidence variants
- telemetry ingestion pipelines
- the FMI placeholder contract is already modeled as a first-class placeholder exchange surface
- a graph database projection
- a full workflow engine

Those items belong in later iterations.
