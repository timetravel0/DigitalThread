# Master Improvement Roadmap

This roadmap is for future coding agents. It focuses on the current workspace-level gaps and on work that improves both projects together.

## WSP-01 - Align frontend navigation with backend route capabilities
- Problem: the web app contains many advanced sections, so profile-specific visibility must stay synchronized with the API surface.
- Benefit: first-time users see a smaller, trustworthy product surface.
- Priority: High
- Effort: M
- Impact: High
- Area: UX / architecture
- Files: `apps/web/lib/tabConfig.ts`, `apps/web/components/project-tab-nav.tsx`, `apps/web/app/projects/[id]/[[...section]]/page.tsx`
- Dependencies: none
- Risks: hiding too much can make expert workflows harder to find.
- Completion criterion: every visible tab maps to a route that is usable for the current profile.
- Instructions for future agents: verify route availability before exposing a tab in the default experience.

## WSP-02 - Reduce duplication between web forms and API payloads
- Problem: many forms still marshal payloads as generic objects and mirror backend payloads manually.
- Benefit: fewer runtime mismatches and clearer form behavior.
- Priority: High
- Effort: M
- Impact: High
- Area: DX / functional reliability
- Files: `apps/web/components/*form.tsx`, `apps/web/lib/api-client.ts`, `apps/api/app/schemas.py`
- Dependencies: route stability and payload contracts.
- Risks: over-abstracting can make simple forms harder to maintain.
- Completion criterion: the most-used forms use shared typed helpers and give explicit validation errors.
- Instructions for future agents: keep the user-facing flow first; do not centralize forms if it reduces clarity.

## WSP-03 - Improve end-to-end smoke coverage for the full thread flow
- Status: Implemented in the web smoke suite at `apps/web/tests/smoke.test.mjs`.
- Problem: the repository has broad API coverage, but the frontend still relies mostly on build/lint/type-check for confidence.
- Benefit: safer changes to cockpit, project navigation, and forms.
- Priority: Medium
- Effort: M
- Impact: High
- Area: test
- Files: `apps/web/app/**`, `apps/web/components/**`
- Dependencies: stable navigation and seed data.
- Risks: brittle tests if route text changes too often.
- Completion criterion: a smoke test can create a project, open a project, and reach requirements/blocks/tests/traceability.
- Instructions for future agents: prefer a small number of realistic user-path tests over many shallow component tests.

## WSP-04 - Strengthen interoperability contracts beyond contract-shaped surfaces
- Problem: SysML mapping, STEP AP242, and FMI are useful projections, but still not native standards runtimes.
- Benefit: external tools can integrate with less manual interpretation.
- Priority: Medium
- Effort: L
- Impact: High
- Area: architecture / integration
- Files: `apps/api/app/services/registry_service.py`, `apps/api/app/services/fmi_service.py`, related federation routes and web views
- Dependencies: stable export contracts.
- Risks: scope creep into full standards engine work.
- Completion criterion: one interoperability surface can be implemented as a real adapter without changing the UI contract.
- Instructions for future agents: keep the contract-shaped UI stable while improving the backend adapter behind it.

## WSP-05 - Consolidate project analysis and cockpit summaries
- Problem: project home, dashboard, and detail pages each summarize the thread differently.
- Benefit: a single mental model for what is populated, missing, and next.
- Priority: Medium
- Effort: M
- Impact: Medium
- Area: UX / product coherence
- Files: `apps/web/components/project-health-card.tsx`, `apps/web/components/dashboard-views.tsx`, `apps/web/app/projects/[id]/[[...section]]/page.tsx`
- Dependencies: tab stats and dashboard summaries.
- Risks: duplicated summary logic if the cockpit and dashboard diverge.
- Completion criterion: the same core counts and next-step logic are reused consistently.
- Instructions for future agents: keep the project cockpit authoritative for project-level orientation.

## WSP-06 - Add stronger trust model and audit hardening
- Problem: the platform has integrity summaries, but not a full cryptographic trust model.
- Benefit: stronger confidence in release history and evidence lineage.
- Priority: Low
- Effort: L
- Impact: Medium
- Area: security / data integrity
- Files: `apps/api/app/services/registry_service.py`, `apps/api/app/models.py`, `apps/web/components/project-health-card.tsx`
- Dependencies: revision snapshot and approval history behavior.
- Risks: over-engineering may slow down the MVP.
- Completion criterion: release and history views can detect and explain tamper evidence consistently.
- Instructions for future agents: keep the current hash-chain summary intact and build from there.

## Note for the Next Coding Agent
1. Read `docs/WORKSPACE_OVERVIEW.md` and the relevant project roadmap before touching code.
2. Confirm whether the change affects `apps/api`, `apps/web`, or both.
3. Prefer small, composable changes over parallel systems.
4. Validate with the project-specific commands before expanding scope.
5. Avoid exposing advanced features in the default UX unless they are fully usable.
