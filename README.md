# ThreadLite

ThreadLite is a lightweight Digital Thread web application for engineering projects.

It is designed for SMEs that need traceability without adopting a heavy PLM or MBSE suite. The MVP starts with a realistic drone project and focuses on the core digital-thread loop:

- define projects
- capture requirements, components, tests, operational runs, and change requests
- create traceability links between objects
- version key records
- build baselines
- inspect coverage, impact, and matrix views

## Why this is a lightweight Digital Thread MVP

ThreadLite is intentionally narrow in scope:

- one project-centric data model
- explicit traceability links instead of a complex graph platform
- simple version fields and baseline snapshots
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
- Project pages with tabs for requirements, components, tests, operational runs, links, matrix, baselines, and change requests
- Requirement, component, and test detail pages with inbound/outbound traceability
- Traceability matrix with component or test columns
- Impact analysis with direct and two-hop traversal
- Baselines for freezing a versioned snapshot of core objects
- Change requests with impact summaries
- Demo seed for a drone inspection project

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

The local launcher waits for the API health check before starting the frontend, so you do not hit a false `Failed to fetch` error during boot.

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

## Development Notes

- The compose file is configured for local development and mounts the repository into the frontend and backend containers.
- The backend container expects a FastAPI application under `apps/api`.
- The frontend container expects a Next.js application under `apps/web`.
- The local script uses SQLite by default and creates `apps/api/threadlite.db` on first run.
- The Docker workflow uses the root `.env.example` and PostgreSQL.
- The local workflow uses `apps/api/.env.example` and `apps/web/.env.local.example`.
- If you are extending the app, keep the API contract consistent with the route names described in the product brief.

## Seeding

The demo seed should create:

- project `DRONE-001` named `Inspection Drone MVP`
- five requirements
- five components
- four test cases
- sample traceability links
- failed and passing test runs
- one operational run
- one baseline
- one change request and its impact records

The seed should make the dashboard immediately useful and populate matrix and impact views with realistic data.

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
