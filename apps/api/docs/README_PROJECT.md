# ThreadLite API Project

## Purpose
ThreadLite API is the backend service for the Digital Thread workspace. It owns the business rules, persistence, workflow transitions, federation, export/import, and seed data used by the frontend.

## Identity
- Path root: `apps/api`
- Type: backend service
- Stack: FastAPI, SQLModel, Alembic, Pydantic, PostgreSQL, Pytest

## Main responsibilities
- expose the HTTP API used by the web app
- persist projects, requirements, blocks, tests, evidence, baselines, change requests, and federation data
- compute dashboards, matrix views, impact views, and contract-shaped projections
- seed realistic demo data for the product

## Relevant folders
- `app/` - API routes, schemas, models, service layer, seed logic
- `app/services/` - domain service modules
- `alembic/` - migrations
- `tests/` - HTTP and service tests
- `docs/` - backend-oriented analysis and planning docs

## Setup and commands
```bash
python -m pip install -e ".[dev]"
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
python -m pytest -q
python -m compileall .
```

## Related documents
- `docs/FUNCTIONAL_ANALYSIS.md`
- `docs/TECHNICAL_ANALYSIS.md`
- `docs/DEPLOYMENT.md`
- `docs/API_REFERENCE.md`
- `docs/DATA_MODEL.md`
- `docs/SECURITY_NOTES.md`
- `docs/TESTING_STRATEGY.md`
- `docs/IMPROVEMENT_ROADMAP.md`
