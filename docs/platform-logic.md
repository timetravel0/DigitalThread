# ThreadLite Platform Logic Guide

This guide explains how ThreadLite works internally.

## 1. Core Principle

ThreadLite is a project-centric engineering workspace.

The platform keeps four ideas separate:

- authored objects, such as requirements, blocks, and test cases
- execution records, such as test runs and operational runs
- reusable evidence, such as `VerificationEvidence`
- configuration snapshots, such as baselines and configuration contexts

Keeping those concerns separate makes the platform easier to reason about and safer to extend.

## 2. Data Flow

The usual data flow is:

1. create a project
2. author requirements, blocks, test cases, components, and relations
3. submit selected authored objects for review
4. approve the objects that are ready
5. capture evidence, test runs, operational runs, and change requests
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

## 6. Verification Logic

Verification uses a layered model:

- `TestRun` records the execution of a test case
- `OperationalRun` records field or mission evidence
- `VerificationEvidence` stores reusable evidence objects that can point to requirements, tests, components, and later simulation or telemetry inputs

Why this matters:

- execution records answer “what happened”
- evidence answers “what can we reuse and review”

The requirement verification status engine derives the current state from linked evidence and test results.

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

The platform does not implement the full SysML specification.
It implements just enough semantics to support practical aerospace authoring and review.

## 12. Seed Logic

The seeded drone project is intentionally structured to exercise the main platform rules:

- requirements cover endurance, video, environment, obstacle detection, and telemetry
- blocks show logical and physical structure
- components map realization
- tests provide verification
- evidence and runs show closed-loop behavior
- a change request and a baseline demonstrate review control

The seed is designed to make the dashboard, matrix, graph, SysML, and export views useful immediately.

## 13. Export Logic

The export bundle is a deterministic JSON package.

It includes:

- project metadata
- authored objects
- execution records
- evidence
- traceability relations
- baselines and change records
- revision snapshots
- configuration context data

Why this matters:

- external tools can validate the result without needing the UI
- the bundle can serve as an audit or handoff artifact

## 14. Local Runtime Logic

ThreadLite supports two runtime modes:

- Docker Compose with PostgreSQL
- direct local execution with SQLite

The local mode is intentionally simple so developers can work without a database server.

## 15. Documentation Logic

The repository documentation is surfaced inside the application as a built-in manual.

That means:

- the UI reads the markdown files stored in the repository
- the docs section is part of the application, not a separate site
- the user guide should remain aligned with the actual screens and flows
- the platform logic guide should remain aligned with the backend rules

## 16. What Is Intentionally Deferred

The platform does not yet implement:

- a full SysML editor
- a full status engine for all evidence variants
- simulation-specific evidence subtypes
- telemetry ingestion pipelines
- a graph database projection
- a full workflow engine

Those items belong in later iterations.
