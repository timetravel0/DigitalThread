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
- inspect coverage, impact, matrix, and SysML practice views

## Why this is a lightweight Digital Thread MVP

ThreadLite is intentionally narrow in scope:

- one project-centric data model
- explicit traceability links instead of a complex graph platform
- simple version fields plus revision snapshots for authored objects
- approval workflow for requirements, blocks, and test cases
- authoritative metadata federation rather than file duplication
- one-hop plus two-hop impact analysis
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

- Dashboard with KPIs and recent activity
- Project pages with tabs for requirements, blocks, tests, operational runs, traceability, SysML, review queue, matrix, baselines, and change requests
- Project pages with an Authoritative Sources registry for connectors, external artifacts, artifact links, and configuration contexts
- Requirement, block, and test detail pages with inbound/outbound traceability plus workflow controls
- Requirement, block, and test detail pages with linked external sources for federated metadata visibility
- Traceability matrix with component or test columns
- Impact analysis with direct and two-hop traversal across requirements, blocks, and tests
- Baselines for freezing approved versions of core objects
- Change requests with impact summaries
- Project export bundles for external validation
- Demo seed for a drone inspection project

## Implemented SysML-Inspired Concepts

ThreadLite does not implement the full SysML standard. It implements a focused subset that is easy to learn:

- Requirement: a statement of need or constraint.
- Block: a SysML-inspired structural element for a logical or physical subsystem.
- Containment: a block hierarchy using `contains` / `composed_of`.
- Satisfy: a block fulfills a requirement.
- Verify: a test case verifies a requirement.
- DeriveReqt: one requirement is derived from another requirement.

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
- sample traceability links
- failed and passing test runs
- one operational run
- one baseline
- one change request and its impact records

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
