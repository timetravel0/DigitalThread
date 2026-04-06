# API Reference

This is a route-group reference, not a generated OpenAPI dump.

## Health and dashboard
- `GET /api/health` - health check
- `GET /api/dashboard` - global dashboard summary
- `GET /api/projects/{project_id}/dashboard` - project dashboard summary
- `GET /api/projects/{project_id}/tab-stats` - project section counts
- `GET /api/projects/{project_id}/authoritative-registry-summary` - registry integrity summary

## Projects
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PUT|PATCH /api/projects/{project_id}`
- `GET /api/projects/{project_id}/export`

## Core thread objects
- Requirements: list, create, detail, update, review transitions, history
- Blocks: list, create, detail, update, review transitions, history, containments
- Components: list, detail, update
- Test cases: list, create, detail, update, review transitions, history
- Test runs: list, create

## Evidence and runs
- Verification evidence: list, create, detail
- Simulation evidence: list, create, detail
- Operational evidence: list, create, detail
- Operational runs: list, create, detail, update

## Traceability and review
- `GET|POST /api/links`
- `DELETE /api/links/{link_id}`
- `GET|POST /api/sysml-relations`
- `DELETE /api/sysml-relations/{relation_id}`
- `GET|POST /api/block-containments`
- `DELETE /api/block-containments/{containment_id}`
- `GET /api/review-queue`

## Baselines and change control
- `GET|POST /api/baselines`
- `GET /api/baselines/{id}`
- `POST /api/baselines/{id}/release`
- `POST /api/baselines/{id}/obsolete`
- `GET /api/baselines/{id}/compare/{context_id}`
- `GET /api/baselines/{id}/compare-baseline/{other_id}`
- `GET /api/change-requests`
- `POST /api/change-requests`
- `GET /api/change-requests/{id}`
- `PATCH /api/change-requests/{id}`
- lifecycle actions for analysis, approve, reject, implement, close, reopen
- `GET|POST /api/change-impacts`

## Federation and configuration
- connectors
- external artifacts
- external artifact versions
- artifact links
- configuration contexts
- configuration item mappings
- configuration comparisons and bridge views

## Interoperability and imports
- SysML block tree, satisfaction, verification, derivations, mapping contract
- STEP AP242 contract
- FMI contracts
- JSON / CSV project imports

## Error and payload behavior
- request validation is handled with Pydantic schemas
- route handlers normalize errors into HTTP 400/404/500 responses through `api_error`
- deletes usually return HTTP 204 with no body
