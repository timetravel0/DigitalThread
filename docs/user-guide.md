# ThreadLite User Guide

This guide explains how to use ThreadLite module by module.

## 1. Start Here

ThreadLite has two starting points:

- open the seeded drone project to explore a complete example
- create a new blank project from scratch and author your own engineering content

The main navigation pattern is:

1. go to the dashboard or project list
2. open a project workspace
3. use the project tabs to move between modules
4. open a detail page when you need to edit, approve, or inspect history

You can open the built-in manual at any time from the left navigation using `Documentation`.

## 2. Dashboard

What it shows:

- projects summary
- requirements coverage KPIs
- failed tests
- a simple distribution of verification states
- a manager / engineering switch for different review perspectives
- recent change requests
- recent test runs

How to use it:

- check whether the workspace already contains enough data to review
- use the seed button when you want the drone demo populated
- use the metrics to spot gaps, risk, or missing coverage

## 3. Projects

What it does:

- lists all projects
- lets you open an existing project
- lets you create a blank project

How to use it:

1. open `Projects`
2. select an existing project or create a new one
3. use project code, name, and description to define the scope

## 4. Project Workspace

The project workspace is the main working area.

Tabs you will use:

- `Overview` for summary KPIs and quick links
- `Requirements` for requirement authoring
- `Blocks` for SysML-inspired structural elements
- `Components` for realization objects
- `Software` for explicit software realization traceability
- `Tests` for verification test cases and runs
- `Simulation Evidence` for model-based evidence records
- `Operational Evidence` for field or telemetry batches
- `Operational Runs` for field evidence
- `Traceability` for links between engineering objects
- `Graph` for visual relationship exploration
- `SysML` for block structure, satisfaction, verification, and derivation views
- `Review Queue` for items waiting for approval
- `Validation` for a lightweight validation cockpit with dropdowns and immediate alerts
- `Matrix` for requirement coverage analysis
- `Baselines` for approved snapshots
- `Change Requests` for change control
- `Non-Conformities` for issue tracking
- `Authoritative Sources` for external tool references and configuration contexts
- `Import` for JSON and CSV ingestion into external artifacts and verification evidence

## 5. Requirements

What requirements are for:

- capture the engineering need or constraint
- define how the system should behave
- drive traceability to blocks, tests, evidence, and change requests

How to use them:

1. open the `Requirements` tab
2. create a new requirement or open an existing one
3. fill in key, title, description, category, priority, and verification method
4. submit the requirement for review when it is ready
5. approve, reject, or create a new draft version from an approved item

Important detail:

- approved requirements are immutable in place
- if a requirement changes after approval, create a draft version instead of editing the approved record directly
- the approval status and the computed verification status are different things
- the requirement page includes a "Why this status?" panel to explain the computed verification result
- when no evidence exists yet, the page explains what to do next and why the requirement is still not covered

## 6. Blocks

What blocks are for:

- model logical or physical system structure
- represent subsystems, assemblies, or software-related architecture elements
- support SysML-inspired containment, satisfy, and derivation semantics

How to use them:

1. open the `Blocks` tab
2. create a block and choose whether it is logical or physical
3. define containment relationships for structure
4. open the block detail page to review links, history, and workflow actions

Useful labels:

- `Block (SysML-inspired structural element)`
- `contains`

Logical vs Physical Toggle:

- `Logical` shows architecture intent and subsystem decomposition
- `Physical` shows realization-oriented blocks and implementation structure
- `All layers` shows both views together

How to use it:

1. open the `Blocks` tab or `SysML -> Block Structure`
2. switch between `Logical`, `Physical`, and `All layers`
3. use the filtered view to inspect either design intent or physical realization

The toggle only filters the view. It does not change the underlying model.
- `satisfies`
- `verified by`

## 7. Components

What components are for:

- capture realization objects such as parts, software modules, sensors, or hardware assemblies
- support flexible metadata through key/value JSON fields

How to use them:

1. open the `Components` tab
2. create or inspect component records
3. use metadata for supplier, part number, firmware, or other project-specific details
4. link components to requirements and tests for traceability

## 7.1 Software

What software is for:

- surface software modules as a distinct realization layer instead of hiding them in a generic component list
- show which requirements, blocks, and evidence point to the software module
- keep repository metadata visible so the software thread is understandable in review

How to use it:

1. open the `Software` tab
2. inspect the software modules in the project
3. open a software module detail page to inspect repository metadata, traceability, and evidence
4. use the component form with `software_module` type when you want to author a new software realization artifact

## 8. Test Cases

What test cases are for:

- define verification activities
- store the expected method and the verification intent
- keep a history of executed test runs

How to use them:

1. open the `Tests` tab
2. create a test case
3. submit it for review when the procedure is ready
4. approve it before using it as a baseline or verification reference
5. add test runs when results become available

## 9. Test Runs

What test runs are for:

- record the actual execution of a test case
- store result, measured values, notes, and executor

How to use them:

1. open a test case detail page
2. add a run after execution
3. inspect the latest result and run history

## 10. Operational Runs

What operational runs are for:

- capture field results, mission observations, and lightweight telemetry
- keep operational data separate from formal test execution records

How to use them:

1. open `Operational Runs`
2. create a run for a mission or field trial
3. attach telemetry JSON and notes when needed
4. link the run to requirements if it supports traceability

## 11. Operational Evidence

What operational evidence is for:

- capture reviewable field or telemetry batches as reusable evidence records
- keep operational evidence separate from raw operational runs
- link the batch to requirements and supporting verification evidence

How to use it:

1. open `Operational Evidence` in the project workspace
2. create a batch from a field observation or telemetry summary
3. link it to the relevant requirement and any supporting verification evidence
4. open the operational evidence detail page to inspect the batch metadata and links

## 12. Simulation Evidence

What simulation evidence is for:

- capture model-based verification results as reusable records
- keep simulation semantics separate from generic verification evidence and raw test runs
- store the model reference, scenario, inputs, expected behavior, observed behavior, result, and execution timestamp

How to use it:

1. open the `Simulation Evidence` tab in a project workspace
2. create a simulation evidence record for a requirement or test case
3. link the record to the relevant requirement, test case, or supporting verification evidence
4. open the simulation evidence detail page to review the captured fields and related objects

## 13. FMI Placeholder Contract

What the FMI placeholder contract is for:

- store a lightweight model reference contract for simulation interoperability
- keep the contract separate from simulation evidence so the model reference can be reused
- give simulation evidence a named contract record to point at when needed

How to use it:

1. open the `FMI` tab in a project workspace
2. create a placeholder contract with the model identifier, version, and adapter profile
3. open a simulation evidence record and link it to the contract when you want an explicit model reference
4. open the contract detail page to review its linked simulation evidence

## 14. Verification Evidence

What evidence is for:

- store reusable evidence objects that are distinct from raw execution records
- link requirements, test cases, components, and later simulation or telemetry inputs

How to use it:

1. open the evidence section on a requirement or test page
2. create evidence from a test result, simulation output, inspection, or telemetry source
3. link it to the relevant requirement and test case
4. reuse the same evidence record when you need to reference it in review or export workflows
5. define telemetry thresholds in the requirement when you want the platform to close the loop automatically
6. use the computed verification badge on the requirement detail page to see whether the requirement is `verified`, `partially_verified`, `at_risk`, `failed`, or `not_covered`
7. note that verification evidence is evaluated first, with telemetry thresholds, simulation evidence, and operational evidence also participating before test or operational runs are treated as fallback
8. inspect the "Why this status?" panel to see the decision source and the main reasons behind the computed result

## 14. Traceability

What traceability does:

- connects authored objects across requirements, blocks, tests, runs, and evidence
- keeps relationships explicit and inspectable

How to use it:

1. open `Traceability`
2. create or inspect links between objects
3. open the matrix if you want a coverage-oriented view
4. open the graph if you want a network-style exploration

## 15. Graph View

What it shows:

- a compact relationship explorer for the chosen focus, including requirements, blocks, CAD parts, software modules, tests, runs, evidence, and changes
- focus filters that let you reduce the view when you want less density
- click-to-isolate behavior that opens a focused graph with separate Incoming / Focus / Outgoing columns
- readable link explanations on each connection so you can see why the relation exists, with visible edge ports on the box boundary and extra spacing when multiple links connect the same pair of objects
- direct links to open the related object detail pages

How to use it:

1. open `Graph`
2. choose a focus mode when you want to narrow the network
3. use `Core traceability` for the default review-oriented view
4. use `All` when you want to inspect the entire project network
5. click any box to open a focused graph for that object and its connected thread, with separated link tracks, CAD part nodes, software realization nodes, and clearer labels

Tip:

- collapse the left navigation when you want more horizontal space

## 16. Relationship Registry

What it shows:

- requirements in one place with their authored status
- generic traceability links, SysML relations, and artifact links
- verification, simulation, and operational evidence records
- filter buttons so you can switch between requirements, links, and evidence

How to use it:

1. open `Registry`
2. switch between `All`, `Requirements`, `Links`, and `Evidence`
3. when you are in `Links`, narrow to generic links, SysML relations, or artifact links
4. when you are in `Evidence`, narrow to verification, simulation, or operational evidence
5. click a requirement or evidence record to open its detail page

## 17. SysML Practice Views

The SysML section is educational rather than a full SysML editor.

Views:

- `Block Structure` shows containment and block hierarchy
- `Satisfaction` shows which blocks satisfy which requirements
- `Verification` shows which test cases verify which requirements
- `Derivations` shows requirement-to-requirement derivation chains
- `Mapping Contract` shows the current model as explicit SysML v2-inspired requirement, block, satisfy, verify, deriveReqt, and contain mappings
- `STEP AP242` shows the placeholder contract for parts, part numbers, and `cad_part` external artifacts

How to use them:

1. open `SysML`
2. switch between the five views
3. use the labels to learn the meaning of each relation
4. open `STEP AP242` when you want to inspect the part-oriented placeholder contract

## 17. Matrix View

What it shows:

- requirements as rows
- components or tests as columns
- cells that indicate whether a relation exists

How to use it:

1. open `Matrix`
2. switch between component and test mode
3. filter by requirement status or category when needed
4. click a cell to inspect the linked objects

## 18. Baselines

What baselines are for:

- capture approved content at a point in time
- preserve object versions for later comparison or audit
- mark a baseline as released when you want follow-up edits to generate a change-request trail automatically
- review lifecycle history for release and obsolescence decisions

How to use them:

1. open `Baselines`
2. create a baseline from approved objects
3. open a baseline detail page to inspect included items
4. release or obsolete the baseline when the review gate changes
5. inspect the lifecycle history to see how the decision was made
6. compare the baseline with another baseline or configuration context when needed

## 19. Change Requests

What change requests are for:

- capture a proposed change
- track impacted objects and severity
- support analysis, disposition, implementation, and closure workflow
- move an open or rejected item directly back into analysis when it is ready for review again

How to use them:

1. open `Change Requests`
2. create a change request
3. add impacted objects
4. review the impact summary before implementation
5. use the lifecycle summary on the detail page to follow analysis, disposition, implementation, and closure notes
6. use the impact map on the detail page to see affected objects grouped by impact level

## 20. Non-Conformities

What non-conformities are for:

- track engineering issues, defects, or observations that need analysis
- record a deviation decision with an explicit `Accept`, `Rework`, or `Reject` disposition
- link the issue back to the affected requirement so reviewers can see the original context
- review the audit trail to see when the NCR status and disposition changed

How to use them:

1. open `Non-Conformities`
2. create a record for the issue
3. attach evidence and impacted objects
4. choose a deviation disposition when the review team decides how to handle it
5. move the item through its lifecycle as analysis progresses
6. use the audit trail section to review the decision history

## 21. Authoritative Sources

What this area is for:

- register external tools and authoritative version pointers
- connect ThreadLite objects to DOORS, MBSE, PLM, or simulation sources
- review revision snapshot integrity for the internal AST history

How to use it:

1. open `Authoritative Sources`
2. define connectors and external artifacts
3. link internal objects to external versions
4. use configuration contexts to combine internal and external references in one review gate
5. check the revision snapshot integrity card to confirm the internal history chain is intact

## 22. Import

What import is for:

- ingest external artifacts and verification evidence from JSON or CSV text
- keep import lightweight and reviewable instead of introducing a file upload workflow
- seed or synchronize data from other tools without leaving the workspace

How to use it:

1. open `Import` in a project workspace
2. paste JSON or CSV content into the form
3. include a `record_type` of `external_artifact` or `verification_evidence` for each row or object
4. include requirement or test case links on verification evidence rows
5. submit the import and inspect the created records in the result panel

## 23. Validation

What validation is for:

- give non-technical reviewers a quick way to check a requirement without reading the full backend model
- show immediate alerts based on the selected requirement's verification criteria and current evidence
- highlight release-gate issues when a requirement is part of a released baseline

How to use it:

1. open `Validation` in a project workspace
2. choose a target requirement
3. choose a validation focus such as mission, power, thermal, evidence, or release gate
4. press `Start Validation`
5. inspect the summary, threshold checks, and alert cards

## 24. Export

What export does:

- creates a deterministic JSON bundle of the project
- includes core objects, evidence, configuration history, and review history
- supports external validation, review, or handoff

How to use it:

1. open a project workspace
2. click `Export JSON`
3. send the bundle to another tool or environment for validation

## 25. Common Workflows

### Explore the seeded demo

1. open the dashboard
2. seed the drone project
3. open the project workspace
4. follow the story in order: mission need -> architecture -> evidence -> change
5. inspect requirements, blocks, tests, matrix, graph, and SysML views
6. open a requirement or change request to inspect the impact map

### Author a new project

1. create a blank project
2. define requirements
3. define blocks and components
4. define test cases
5. create traceability links and SysML relations
6. add evidence and operational runs
7. create a baseline
8. export the bundle

### Run an approval cycle

1. create the object in draft
2. submit it for review
3. approve or reject it
4. create a new draft version if the approved item needs changes

## 25. What ThreadLite Is Not

ThreadLite is not:

- a full SysML modeling tool
- a full enterprise PLM suite
- a full ALM suite
- a graph database product

It is a lightweight engineering workspace that keeps traceability, approval, evidence, and configuration under one roof.
