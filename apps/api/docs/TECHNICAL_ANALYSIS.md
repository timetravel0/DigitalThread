# Technical Analysis

## Stack
- FastAPI application in `app/main.py`
- SQLModel ORM in `app/models.py`
- Pydantic schemas in `app/schemas.py`
- Alembic migrations under `alembic/`
- Pytest suite under `tests/`
- PostgreSQL supported through `DATABASE_URL`
- SQLite used for local development by default

## Entrypoints and bootstrap
- `app/main.py` wires the FastAPI app, CORS, startup DB initialization, and all HTTP routes.
- `app/db.py` provides the session factory and database initialization.
- `app/core/__init__.py` loads settings from environment variables.

## Service architecture
- `app/services/` contains the domain service modules.
- `app/services/__init__.py` re-exports the public service API for backward compatibility.
- `_common.py` hosts shared helpers and object registry logic.
- `app/services_legacy.py` remains as the backing implementation used during the refactor transition.
- `app/impact_service.py` and `app/seed_service.py` are standalone facades for impact and seeding workflows.

## Main technical patterns
- routers are thin and delegate to service functions
- schema validation happens at the API boundary
- domain logic is centralized in services rather than inside route handlers
- workflow and history changes are recorded in revision snapshots and approval logs
- import/export and federation are handled server-side, not in the frontend

## Integration surfaces
- `/api/*` endpoints consumed by the web app
- CORS is configured from `CORS_ORIGINS`
- project export bundles provide a deterministic JSON package for external validation
- seed endpoints populate realistic demo data for the UI and tests

## Quality observations
- the route surface is broad, so `app/main.py` is still a large coordination file
- the service layer is modular now, but the domain remains rich and interconnected
- API contracts are explicit, but some interoperability views are still contract-shaped projections
- backend tests are strong at the HTTP and service layer, but the codebase still benefits from more end-to-end coverage

## Scalability and maintainability notes
- the current design is easier to maintain than a single monolith, but the number of routes and domain objects is still large
- relation and evidence management are domain-heavy, so future changes should stay close to the service modules and test coverage
- any new endpoint should be mirrored in the frontend API client and docs to avoid drift
