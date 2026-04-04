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
- `Tests` for verification test cases and runs
- `Operational Runs` for field evidence
- `Traceability` for links between engineering objects
- `Graph` for visual relationship exploration
- `SysML` for block structure, satisfaction, verification, and derivation views
- `Review Queue` for items waiting for approval
- `Matrix` for requirement coverage analysis
- `Baselines` for approved snapshots
- `Change Requests` for change control
- `Non-Conformities` for issue tracking
- `Authoritative Sources` for external tool references and configuration contexts

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

## 11. Verification Evidence

What evidence is for:

- store reusable evidence objects that are distinct from raw execution records
- link requirements, test cases, components, and later simulation or telemetry inputs

How to use it:

1. open the evidence section on a requirement or test page
2. create evidence from a test result, simulation output, inspection, or telemetry source
3. link it to the relevant requirement and test case
4. reuse the same evidence record when you need to reference it in review or export workflows

## 12. Traceability

What traceability does:

- connects authored objects across requirements, blocks, tests, runs, and evidence
- keeps relationships explicit and inspectable

How to use it:

1. open `Traceability`
2. create or inspect links between objects
3. open the matrix if you want a coverage-oriented view
4. open the graph if you want a network-style exploration

## 13. Graph View

What it shows:

- a connected view of requirements, blocks, parts, tests, runs, evidence, and changes

How to use it:

1. open `Graph`
2. choose a focus filter such as requirements, blocks, tests, or evidence
3. click nearby objects to understand the local impact pattern

Tip:

- collapse the left navigation when you want more horizontal space

## 14. SysML Practice Views

The SysML section is educational rather than a full SysML editor.

Views:

- `Block Structure` shows containment and block hierarchy
- `Satisfaction` shows which blocks satisfy which requirements
- `Verification` shows which test cases verify which requirements
- `Derivations` shows requirement-to-requirement derivation chains

How to use them:

1. open `SysML`
2. switch between the four views
3. use the labels to learn the meaning of each relation

## 15. Matrix View

What it shows:

- requirements as rows
- components or tests as columns
- cells that indicate whether a relation exists

How to use it:

1. open `Matrix`
2. switch between component and test mode
3. filter by requirement status or category when needed
4. click a cell to inspect the linked objects

## 16. Baselines

What baselines are for:

- capture approved content at a point in time
- preserve object versions for later comparison or audit

How to use them:

1. open `Baselines`
2. create a baseline from approved objects
3. open a baseline detail page to inspect included items
4. compare the baseline with another baseline or configuration context when needed

## 17. Change Requests

What change requests are for:

- capture a proposed change
- track impacted objects and severity
- support analysis and implementation workflow

How to use them:

1. open `Change Requests`
2. create a change request
3. add impacted objects
4. review the impact summary before implementation

## 18. Non-Conformities

What non-conformities are for:

- track engineering issues, defects, or observations that need analysis

How to use them:

1. open `Non-Conformities`
2. create a record for the issue
3. attach evidence and impacted objects
4. move the item through its lifecycle as analysis progresses

## 19. Authoritative Sources

What this area is for:

- register external tools and authoritative version pointers
- connect ThreadLite objects to DOORS, MBSE, PLM, or simulation sources

How to use it:

1. open `Authoritative Sources`
2. define connectors and external artifacts
3. link internal objects to external versions
4. use configuration contexts to combine internal and external references in one review gate

## 20. Export

What export does:

- creates a deterministic JSON bundle of the project
- supports external validation, review, or handoff

How to use it:

1. open a project workspace
2. click `Export JSON`
3. send the bundle to another tool or environment for validation

## 21. Common Workflows

### Explore the seeded demo

1. open the dashboard
2. seed the drone project
3. open the project workspace
4. inspect requirements, blocks, tests, matrix, graph, and SysML views

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

## 22. What ThreadLite Is Not

ThreadLite is not:

- a full SysML modeling tool
- a full enterprise PLM suite
- a full ALM suite
- a graph database product

It is a lightweight engineering workspace that keeps traceability, approval, evidence, and configuration under one roof.
