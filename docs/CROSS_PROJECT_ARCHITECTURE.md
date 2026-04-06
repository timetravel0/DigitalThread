# Cross-Project Architecture

## System boundary
ThreadLite is a two-project workspace:
- `apps/api` owns business rules, persistence, workflows, federation, import/export, and seed data.
- `apps/web` owns the user interface, project cockpit, forms, navigation, traceability views, and documentation portal.

## Main communication path
```text
User -> Next.js web app -> FastAPI JSON API -> SQLModel / PostgreSQL
```

## Integration points
- `apps/web/lib/api-client.ts` contains the frontend HTTP client and route wrappers.
- `apps/api/app/main.py` exposes the API routes consumed by the frontend.
- `apps/web/lib/labels.ts` and `apps/web/lib/tabConfig.ts` localize the user experience by profile.
- `apps/web/lib/docs.ts` resolves root markdown files for the in-app documentation portal.
- `apps/api/app/services/` contains the domain service layer that implements the API behavior.

## Shared product concepts
Both projects speak the same digital-thread vocabulary:
- projects
- requirements / specifications / goals
- blocks / components / elements
- tests / checks / verifications
- traceability links and SysML-style relations
- evidence, baselines, and change requests
- federation to external authoritative sources

## Architectural risks
- The frontend contains some profile-aware workflow and navigation logic that must stay aligned with the backend route model.
- The API surface is broad, so route additions can easily outgrow the frontend unless the docs and client are updated together.
- Some interoperability surfaces are deliberately contract-shaped views rather than native standards runtimes.
- The documentation portal depends on repository markdown files, so docs updates are part of the product surface.

## Dependency direction
- `apps/web` depends on `apps/api` for all live data.
- `apps/api` does not depend on `apps/web` at runtime.
- Root docs are shared as repository content and are rendered by the web app.
