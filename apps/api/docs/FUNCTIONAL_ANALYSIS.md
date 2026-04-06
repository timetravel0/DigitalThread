# Functional Analysis

## Functional purpose
The API provides the operational Digital Thread backend for ThreadLite. It is the source of truth for project data, review workflows, traceability links, evidence, baselines, change requests, and interoperability projections.

## Main actors
- Web application in `apps/web`
- Future external API clients
- Test suites and seed workflows
- Migration and deployment tooling

## Core user-facing flows supported by the API
- create, list, view, update, and delete projects
- author requirements, blocks, components, and test cases
- submit items for review, approve them, reject them, and create draft versions
- create traceability links, SysML relations, and block containments
- create and inspect verification, simulation, and operational evidence
- create and manage baselines and configuration contexts
- create and manage change requests and non-conformities
- register connectors, external artifacts, artifact versions, and artifact links
- import external records and export a full project bundle
- seed realistic demo projects

## What is complete today
- project CRUD and dashboard endpoints
- requirement, block, and test case workflows
- evidence capture and detail endpoints
- federation and registry surfaces
- baselines, change requests, configuration contexts, and non-conformities
- SysML-inspired views and contract-shaped projections
- import/export and demo seeding

## What remains partial or deliberately simplified
- no user authentication or role system is visible in the API
- some standards surfaces are projections rather than native standards engines
- the workflow and integrity model is intentionally lighter than an enterprise PLM stack

## Business rules visible in the code
- approved items are treated as immutable in place
- draft versions are created for changes to approved content
- released baselines trigger change-control behavior when linked content changes
- verification status is derived from linked evidence and telemetry-like criteria
- project/profile vocabulary is separate from stored data

## Open questions
- how far the project should go toward native standards adapters instead of projections
- whether auth and authorization should be added before broader external exposure
- whether the review workflow should be generalized across more object types
