# Workspace Overview

## Scope and evidence level
This document is based on the real repository layout, manifests, application entrypoints, and project documentation present in the workspace.

## Real projects in this workspace

| Project | Path | Type | Stack | Role |
|---|---|---|---|---|
| ThreadLite API | `apps/api` | Backend service | FastAPI, SQLModel, Alembic, Pydantic, PostgreSQL, Pytest | Domain API, persistence, workflows, federation, import/export |
| ThreadLite Web | `apps/web` | Frontend application | Next.js 14, React 18, TypeScript, Tailwind CSS, React Hook Form, Zod | User-facing cockpit, forms, docs portal, navigation, analysis views |

## Supporting workspace areas
- `docs/` - product and workspace documentation, including use cases and architecture notes.
- `infra/` - deployment and infrastructure material.
- `scripts/` - local startup and maintenance helpers.
- `docker-compose.yml` - local multi-service entrypoint.

## Boundary notes
- `node_modules/`, `.next/`, `dist/`, `build/`, `coverage/`, `.cache/`, `__pycache__/`, `.pytest_cache/`, and similar generated or dependency directories are excluded from analysis as source code.
- Lock files are useful for environment reproduction, but not as the primary source for functional analysis.

## Cross-project relationship
- `apps/web` consumes the HTTP JSON API exposed by `apps/api`.
- `apps/web/lib/api-client.ts` points at the backend through `NEXT_PUBLIC_API_BASE_URL` or the local default `http://localhost:8000`.
- The docs portal in `apps/web` reads markdown files from the repository root `docs/` directory.
- The two projects share product vocabulary through labels, tab visibility, and route naming, but they do not share runtime code.

## Workspace documentation map
- Root product overview: `README.md`
- Workspace overview: `docs/WORKSPACE_OVERVIEW.md`
- Cross-project architecture: `docs/CROSS_PROJECT_ARCHITECTURE.md`
- Master roadmap: `docs/MASTER_IMPROVEMENT_ROADMAP.md`
- API project docs: `apps/api/docs/`
- Web project docs: `apps/web/docs/`
