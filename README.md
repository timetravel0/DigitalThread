# ThreadLite

ThreadLite is a lightweight Digital Thread web application for engineering projects.

It is designed for SMEs that need traceability without adopting a heavy PLM or MBSE suite. The platform now behaves like a small engineering authoring workspace rather than a read-only demo:

- define projects
- create a new blank project from scratch
- create and edit requirements, blocks, and test cases
- submit items for review and approve or reject them
- create traceability links and SysML-inspired relations
- version approved artifacts through draft copies
- build baselines from approved content
- register authoritative external sources and version pointers
- link internal objects to external DOORS, MBSE, PLM, and simulation artifacts
- define configuration contexts that combine internal and external versions
- export a complete project bundle for external validation
- inspect coverage, impact, matrix, SysML practice views, and the STEP AP242 contract-shaped surface

## Documentation Set

ThreadLite documentation is split into a small set of English-language guides:

- [User Guide](docs/user-guide.md) - how to use each module and feature from the UI
- [Platform Logic Guide](docs/platform-logic.md) - how the platform works internally and how the data flows
- [Target Architecture](docs/target-architecture.md) - the intended next architecture layer
- [Implementation Backlog](docs/implementation-backlog.md) - the backlog of planned stories
- [Gap Analysis](docs/gap-analysis.md) - the current capability map and open gaps

Documentation policy:

- every implemented feature should update the root README and the affected docs
- new product behavior should be reflected in the user guide and, when needed, the logic guide
- keep documentation in English only

## In-App Documentation

ThreadLite includes a built-in documentation section inside the application.

- open `Documentation` from the left navigation
- browse the repository manuals without leaving the app
- use `User Guide` for feature usage and `Platform Logic Guide` for the operating model

The in-app documentation is the user-facing manual and should stay synchronized with the repository docs.

## Why this is a lightweight Digital Thread MVP

ThreadLite is intentionally narrow in scope:

- one project-centric data model
- explicit traceability links instead of a complex graph platform
- simple version fields plus revision snapshots for authored objects
- revision snapshots carry content hashes and an integrity summary to make the audit trail harder to tamper with
- approval workflow for requirements, blocks, and test cases
- authoritative metadata federation rather than file duplication
- graph-aware impact analysis with direct, secondary, and evidence-linked traversal
- practical seed data so the product feels alive on first run

The goal is not to replace enterprise PLM/ALM platforms. The goal is to provide a clear foundation that a small engineering team can actually adopt and extend.

## Architecture

```text
+-----------------------------+
|        Next.js Web          |
|  App Router + Tailwind UI   |
|  Forms, tables, matrix UI   |
+--------------+--------------+
               |
               | HTTP / JSON
               |
+--------------v--------------+
|        FastAPI API          |
| SQLModel + Alembic + Pydantic|
| Domain services and rules   |
+--------------+--------------+
               |
               | PostgreSQL
               |
+--------------v--------------+
|          Database           |
|         PostgreSQL          |
+-----------------------------+
```

Repository layout:

```text
threadlite/
  apps/
    api/
    web/
  scripts/
  infra/
  docker-compose.yml
  README.md
```

## Key Product Areas

- Dashboard with manager and engineering views, KPIs, and recent activity
- Project pages with tabs for requirements, blocks, tests, simulation evidence, operational evidence, operational runs, traceability, SysML, STEP AP242, FMI, review queue, validation, matrix, baselines, change requests, and import
- Project pages with a dedicated Software section for explicit software realization traceability
- Project pages with an Authoritative Sources registry for connectors, external artifacts, artifact links, and configuration contexts
- Relationship Registry pages that list requirements, links, and evidence with simple filters
- Requirement, block, and test detail pages with inbound/outbound traceability plus workflow controls
- Requirement, block, and test detail pages with linked external sources for federated metadata visibility
- Verification criteria on requirements so telemetry thresholds can close the loop automatically
- Logical vs physical toggles that let you inspect the drone as architecture intent or physical realization
- Simulation evidence detail and capture surfaces for model/scenario/input/output/result records
- Software realization surfaces for explicit software-module traceability and evidence
- FMI contract-shaped surfaces for simulation model reference metadata
- Operational evidence detail and capture surfaces for field/telemetry batch records linked to requirements and verification evidence
- Project import surface for JSON and CSV external data ingestion into external artifacts and verification evidence
- Traceability matrix with component or test columns
- Relationship registry with filters for requirements, links, and evidence
- Traceability graph with a compact relationship explorer by default and a focused graph when you click an object, showing Incoming / Focus / Outgoing columns, walk-the-thread expansion across requirements, blocks, software realization nodes, CAD parts, tests, and evidence, readable link explanations, visible edge ports on box boundaries, and extra spacing for multiple links between the same objects
- Impact analysis with graph-aware traversal across requirements, blocks, software realization nodes, CAD parts, tests, evidence, baselines, and change requests
- Impact visualization cards on requirement and change request pages so affected objects are easy to scan
- Baselines for freezing approved versions of core objects
- Released baselines create a change-request trail when linked components or requirements are changed
- Change requests with impact summaries and lifecycle notes for analysis, disposition, implementation, and closure, plus direct resubmission to analysis from open or rejected states
- Baselines and configuration contexts with traceable lifecycle history so review decisions are visible across configuration objects
- Non-conformities with explicit Accept / Rework / Reject dispositions
- Project export bundles for external validation
- Demo seed for a drone inspection project
- Domain service modules split along impact and seed workflows, while the legacy service facade remains stable for compatibility

## Verification Status

Requirement verification state is computed from linked `VerificationEvidence` first.

- the requirement detail page shows the computed state clearly
- the requirement detail page includes a reviewer-friendly "Why this status?" panel
- the panel explains whether the result came from verification evidence, telemetry thresholds, simulation evidence, or fallback compatibility logic
- the dashboard shows a simple breakdown of verification states, not just a single risk count
- the dashboard rolls those computed states up into its risk metrics
- compatible test runs and operational runs are used as fallback when evidence is neutral
- approval and review status remain separate from verification status

## Impact Visualization

Requirement and change request pages now include a compact impact map instead of a plain list.

- the root object appears first
- impacted objects are grouped into readable sections
- related baselines and open change requests are shown where relevant
- the result is intentionally smaller and easier to scan than a full graph view

## How To Use The Platform

If you are new to ThreadLite, start here:

1. Open the [User Guide](docs/user-guide.md) for task-oriented instructions by module.
2. Open a project and use the tabs to move between requirements, blocks, tests, traceability, SysML, matrix, baselines, and change requests.
3. Use the detail pages to create, edit, review, and approve engineering objects.
4. Use the registry, matrix, and graph views to understand coverage and connectivity.
5. Use the validation tab when you want a simplified SidSat-style cockpit with dropdown-based alerts.
6. Use the import tab when you need to ingest JSON or CSV data into external artifacts or verification evidence.
7. Use the export bundle when you need a deterministic package for external validation.

The [Platform Logic Guide](docs/platform-logic.md) explains the rules behind these screens so the UI and backend behavior stay understandable together.

## Implemented SysML-Inspired Concepts

ThreadLite does not implement the full SysML standard. It implements a focused subset that is easy to learn:

- Requirement: a statement of need or constraint.
- Block: a SysML-inspired structural element for a logical or physical subsystem.
- Containment: a block hierarchy using `contains` / `composed_of`.
- Logical vs physical toggle: a UI filter that uses `Block.abstraction_level` to show architectural intent or physical realization.
- Satisfy: a block fulfills a requirement.
- Verify: a test case verifies a requirement.
- DeriveReqt: one requirement is derived from another requirement.
- SysML mapping contract: a contract-shaped projection that makes the current requirements, blocks, and relations exportable as SysML v2-inspired concepts.
- STEP AP242 contract-shaped surface: a contract-shaped projection that makes physical part metadata and cad_part artifacts exportable as AP242-style concepts.
- FMI contract-shaped surface: a contract-shaped projection that makes simulation model reference metadata exportable as FMI-style concepts.

In the drone demo, the top-level `Drone System` block contains subsystems such as `Power Subsystem` and `Flight Controller`, while the battery and controller satisfy endurance, telemetry, and temperature requirements.

## Authoritative Sources & Federation

ThreadLite now treats external tools as authoritative source systems rather than data to copy into the app.

- `ConnectorDefinition` registers the owning tool or feed.
- `ExternalArtifact` stores the external object pointer and metadata only.
- `ExternalArtifactVersion` captures the specific revision or version to reference.
- `ArtifactLink` connects internal requirements, blocks, and test cases to external authoritative objects.
- `ConfigurationContext` groups approved internal versions and external artifact versions into a review gate or working snapshot.

This is the key distinction:

- Baseline = frozen internal snapshot of approved ThreadLite objects.
- Configuration Context = broader review or release context that can include internal object versions and external authoritative versions together.

Example mappings in the drone demo:

- `DR-REQ-001` -> external DOORS requirement `REQ-DOORS-001` v7
- `DR-BLK-004` -> external Cameo block `SYSML-BLOCK-BATTERY` v2
- `DR-BLK-004` -> external Teamcenter part `PLM-PART-DR-BATT-01` rev C
- `DR-TST-001` -> external Simulink model `SIM-FLIGHT-ENDURANCE` v1.4

That makes ThreadLite a connective layer across domains, not a replacement for the tools that own the source artifacts.

## Approval Workflow

Requirements, blocks, and test cases move through a simple lifecycle:

- `draft`
- `in_review`
- `approved`
- `rejected`
- `obsolete`

Editing rules:

- draft and rejected items can be edited directly
- approved items are immutable in place
- if you need to change an approved item, create a new draft version from it

The UI makes this explicit: approved requirements, blocks, and test cases show a `Create draft version and edit` action instead of a direct edit flow.

Every authored update records a revision snapshot so the history panel can show the sequence of changes without a full event-sourcing implementation.

## Baselines

Baselines now default to approved content only.

- approved requirements, blocks, and test cases are included by default
- draft and in-review items are skipped unless you explicitly choose them
- each baseline item stores the object version captured at baseline creation time
- this keeps the baseline model simple and makes future comparison features straightforward

## Project Creation and Export

ThreadLite now supports two starting points:

- start from the seeded drone project
- create a blank project from scratch and author everything yourself

Each project can be exported as a single JSON bundle from the project workspace. The export includes:

- project metadata
- requirements
- blocks
- block containments
- components
- test cases
- test runs
- simulation evidence and simulation evidence links
- operational evidence and operational evidence links
- operational runs
- links
- SysML relations
- baselines and baseline items
- change requests and change impacts
- connectors, external artifacts, external artifact versions, artifact links
- configuration contexts and configuration item mappings
- revision snapshots

The export is intentionally deterministic and flat enough that another tool can validate it without needing the web app.

Future federation work will add lightweight import contracts, standards-oriented adapters, and richer configuration comparison, but those are intentionally out of scope for the current MVP.

## Local Setup

ThreadLite supports two local workflows:

- Docker Compose, which brings up PostgreSQL, the API, and the web app together.
- Direct local execution, which uses your installed Python, Node.js, and a local SQLite database file.

### Option 1: Docker Compose

1. Create the root environment file from the example.

```bash
Copy-Item .env.example .env
```

On macOS or Linux, use:

```bash
cp .env.example .env
```

2. Start the stack.

```bash
docker compose up
```

3. Database migrations run automatically when the backend container starts. If you want to rerun them manually:

```bash
docker compose exec backend alembic upgrade head
```

4. Seed the demo project.

```bash
curl -X POST http://localhost:8000/api/seed/demo
```

5. Open the app.

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

### Option 2: Run locally without Docker

Prerequisites:

- Python 3.12
- Node.js 20+
- No database server is required for local development. ThreadLite will create a SQLite file automatically.

1. Create the local env files from the examples.

```bash
Copy-Item apps/api/.env.example apps/api/.env
Copy-Item apps/web/.env.local.example apps/web/.env.local
```

On macOS or Linux, use:

```bash
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.local.example apps/web/.env.local
```

2. Install backend and frontend dependencies.

```bash
cd apps/api
python -m pip install -e ".[dev]"

cd ..\web
npm install
```

3. Run migrations against your local SQLite database file.

```bash
cd ..\api
alembic upgrade head
```

4. Start the backend and frontend.

```bash
cd ..\..
.\scripts\start-local.ps1
```

If your system blocks PowerShell scripts, use the Windows launcher instead:

```bash
.\scripts\start-local.cmd
```

The local launcher opens both windows immediately and prints a warning if the API health check is still warming up, so the frontend does not get blocked by slow local startup.

If you prefer manual terminals instead of the helper script:

```bash
cd apps/api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
cd apps/web
npm run dev
```

5. Seed the demo project.

```bash
curl -X POST http://localhost:8000/api/seed/demo
```

6. Open the app.

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

From the Projects page you can create a blank project from scratch. From any project workspace you can export a full JSON bundle for external validation.

## Development Notes

- The compose file is configured for local development and mounts the repository into the frontend and backend containers.
- The backend container expects a FastAPI application under `apps/api`.
- The frontend container expects a Next.js application under `apps/web`.
- The local script uses SQLite by default and creates `apps/api/threadlite.db` on first run.
- The Docker workflow uses the root `.env.example` and PostgreSQL.
- The local workflow uses `apps/api/.env.example` and `apps/web/.env.local.example`.
- The local launcher opens both backend and frontend windows; if the API is still starting, refresh the frontend once the backend window reports `Application startup complete`.
- If you are extending the app, keep the API contract consistent with the route names described in the product brief.
- Use the project workspace `Export JSON` action when you need a full bundle for audit or external validation.

## Seeding

The demo seed should create:

- project `DRONE-001` named `Inspection Drone MVP`
- six requirements, including one derived requirement
- seven blocks with a simple containment hierarchy
- four test cases
- SysML satisfy, verify, and deriveReqt relations
- a SysML mapping contract export for the seeded model
- a STEP AP242 contract-shaped surface export for the seeded physical parts
- an FMI contract-shaped surface export for the seeded simulation model reference
- sample traceability links
- failed and passing test runs
- one operational run
- one baseline
- one change request and its impact records

The seed is narrated as a simple aerospace review chain: mission need -> architecture -> evidence -> change

- mission need: the drone must cover a 30 minute inspection route and keep reserve
- architecture: logical blocks and physical parts show how the mission is realized
- evidence: test runs, simulation evidence, operational evidence, and verification records show what happened
- change: the endurance shortfall drives a change request and linked impacts

The seed should make the dashboard immediately useful and populate matrix and impact views with realistic data.

The seeded block hierarchy also powers the SysML `Block Structure` view, so the drone project opens with a visible `contains` tree rather than an empty SysML section.

## Screenshots

Placeholder section for future screenshots.

Insert the following once the UI is available:

- dashboard
- project overview
- requirement detail
- component detail
- test detail
- matrix view
- baseline detail
- change request detail

## Roadmap

Future evolutions for ThreadLite:

- user authentication and roles
- file attachments and evidence management
- visual graph explorer
- baseline comparison
- digital twin telemetry ingestion
- notifications and alerts
- graph database projection for larger projects
- import and export from Excel and CSV
- API integrations with PLM and ALM tools

## Testing

Recommended checks once the app code is present:

- backend pytest suite
- frontend component and page tests
- API smoke test for seed and dashboard endpoints

## License

Add project licensing here when the product direction is finalized.

## Workspace Documentation

For workspace-level analysis and maintenance, use:
- `docs/WORKSPACE_OVERVIEW.md`
- `docs/CROSS_PROJECT_ARCHITECTURE.md`
- `docs/MASTER_IMPROVEMENT_ROADMAP.md`

Project-specific analysis lives here:
- `apps/api/docs/`
- `apps/web/docs/`

If you are a future coding agent, start with the project `AGENTS.md` file, then read the project docs before making changes.
