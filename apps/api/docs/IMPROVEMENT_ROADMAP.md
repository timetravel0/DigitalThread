# Improvement Roadmap

## API-01 - Add a real auth boundary
- Problem: the API is currently wide open.
- Benefit: safer external exposure and clearer ownership of write operations.
- Priority: High
- Effort: L
- Impact: High
- Area: security
- Files: `app/main.py`, `app/core/__init__.py`, route handlers, tests
- Dependencies: none
- Risks: auth may require frontend and deployment changes together.
- Completion criterion: protected routes enforce authenticated access and role checks.
- Instructions for future agents: keep route behavior stable while adding auth middleware or dependencies.

## API-02 - Reduce route-module concentration in `app/main.py`
- Problem: route registration is still centralized in one large file.
- Benefit: easier navigation and safer endpoint evolution.
- Priority: Medium
- Effort: M
- Impact: Medium
- Area: architecture
- Files: `app/main.py`, `app/services/`, tests
- Dependencies: service package stability.
- Risks: moving routes too aggressively can create import cycles.
- Completion criterion: route groups are split into router modules without changing behavior.
- Instructions for future agents: move one route family at a time and keep tests green after each move.

## API-03 - Tighten interoperability adapters
- Problem: SysML, AP242, and FMI are still projection-oriented.
- Benefit: better external-tool handoff.
- Priority: Medium
- Effort: L
- Impact: High
- Area: integration
- Files: `app/services/registry_service.py`, `app/services/fmi_service.py`, federation services
- Dependencies: export contract stability.
- Risks: scope creep into standards-engine work.
- Completion criterion: at least one contract can be backed by a real adapter path.
- Instructions for future agents: preserve the contract shape already used by the frontend.

## API-04 - Add pagination or filtering to large list endpoints
- Problem: many list endpoints return whole collections.
- Benefit: safer scaling as projects grow.
- Priority: Medium
- Effort: M
- Impact: Medium
- Area: performance
- Files: list endpoints and service query helpers
- Dependencies: route contracts and client updates.
- Risks: changing list semantics can ripple through the web app.
- Completion criterion: large collections can be queried without fetching everything at once.
- Instructions for future agents: keep the default response compatible for small projects.

## API-05 - Make the history and integrity model stronger
- Problem: revision history exists, but the trust model is still lightweight.
- Benefit: better audit confidence.
- Priority: Low
- Effort: M
- Impact: Medium
- Area: security / data integrity
- Files: `app/services/registry_service.py`, models, history-related service functions
- Dependencies: approval logs and revision snapshots.
- Risks: over-engineering the audit trail too early.
- Completion criterion: integrity checks and history views can explain tamper evidence more clearly.
- Instructions for future agents: keep the current snapshot and approval history behavior intact while extending it.

## Note for the Next Coding Agent
1. Read `README.md` and the project docs before changing code.
2. Decide whether the change is route-level, service-level, or data-model-level.
3. Add or update tests in the smallest relevant test module.
4. Keep `app/services/__init__.py` backward compatible.
5. Avoid introducing new behavior into `app/main.py` unless the route itself is changing.
