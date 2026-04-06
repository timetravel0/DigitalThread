# AGENTS.md

## Scopo
ThreadLite API backend for the Digital Thread domain model, workflows, federation, evidence, and export/import.

## Identita del progetto
- Nome: ThreadLite API
- Path root: `apps/api`
- Tipo: backend service
- Stack principale: FastAPI, SQLModel, Alembic, Pydantic, PostgreSQL, Pytest

## Cartelle rilevanti
- `app/` - API routes, schemas, models, service layer, seed logic
- `app/services/` - domain service modules and shared helpers
- `alembic/` - migrations and migration environment
- `tests/` - HTTP and service tests
- `README.md` - service-layer and backend notes
- `docs/` - project-specific backend analysis docs

## Cartelle da ignorare
- `__pycache__/`
- `.pytest_cache/`
- `.venv/`
- `venv/`
- `threadlite.db`
- `threadlite_api.egg-info/`
- `dist/`
- `build/`
- `.git/`

## Convenzioni osservate
- FastAPI routes are declared in `app/main.py` and delegate to service functions.
- Domain logic is split across `app/services/` and re-exported from `app/services/__init__.py` for backward compatibility.
- SQLModel entities live in `app/models.py`; Pydantic request and response models live in `app/schemas.py`.
- API errors are normalized through `api_error` in `app/main.py`.
- Tests exercise both HTTP routes and service behavior.

## Comandi utili
```bash
# installazione
python -m pip install -e ".[dev]"

# avvio locale
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# test
python -m pytest -q

# lint / type-check
python -m compileall .

# build
python -m compileall .
```

## Guardrail
- Leggi prima `README.md` e `docs/` backend.
- Modifica prima i service modules, poi i schemas, poi i routes.
- Non cambiare le query o il modello dati senza un motivo concreto e test aggiornati.
- Non importare helpers privati direttamente dai router; usa `app.services`.
- Evita di toccare file generati o cache locali.

## Riferimenti alla documentazione
- `README.md`
- `docs/README_PROJECT.md`
- `docs/FUNCTIONAL_ANALYSIS.md`
- `docs/TECHNICAL_ANALYSIS.md`
- `docs/DEPLOYMENT.md`
- `docs/API_REFERENCE.md`
- `docs/DATA_MODEL.md`
- `docs/SECURITY_NOTES.md`
- `docs/TESTING_STRATEGY.md`
- `docs/IMPROVEMENT_ROADMAP.md`
