# Deployment

## Prerequisites
- Python 3.12+
- PostgreSQL if you want a persistent server deployment
- SQLite is acceptable for local development

## Environment variables observed in the repo
- `DATABASE_URL` - database connection string
- `CORS_ORIGINS` - comma-separated list of allowed frontend origins
- `API_HOST` - bind host for local runs
- `API_PORT` - bind port for local runs

The settings loader in `app/core/__init__.py` reads `.env` and ignores extra values.

## Local run
```bash
python -m pip install -e ".[dev]"
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Migrations
- Alembic is the migration mechanism.
- Run `alembic upgrade head` before starting the API against a fresh database.
- The migration history is part of the repository and should be kept in sync with `app/models.py`.

## Production notes
- Use a PostgreSQL `DATABASE_URL`.
- Set `CORS_ORIGINS` to the actual frontend origin(s).
- Run the API behind a process manager or container runtime.
- Keep the seed endpoints disabled or restricted in real deployments if the project should not be publicly writable.

## Rollback considerations
- Database schema changes are managed through Alembic revisions.
- If a deployment fails, rollback must follow the migration history, not just the application code.
