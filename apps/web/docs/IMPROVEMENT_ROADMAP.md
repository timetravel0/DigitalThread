# Improvement Roadmap

## WEB-01 - Break the large project workspace route into smaller domain views
- Problem: `app/projects/[id]/[[...section]]/page.tsx` handles many views and summaries in one route.
- Benefit: easier maintenance and lower risk when changing a single section.
- Priority: High
- Effort: L
- Impact: High
- Area: architecture
- Files: `app/projects/[id]/[[...section]]/page.tsx`, related section components
- Dependencies: stable route and tab behavior.
- Risks: moving too much too fast can break navigation.
- Completion criterion: the workspace still works, but each major section is easier to reason about.
- Instructions for future agents: split one section at a time and preserve URLs.

## WEB-02 - Reduce handwritten API wrapper drift
- Problem: `lib/api-client.ts` mirrors many endpoints manually.
- Benefit: fewer mistakes when backend routes change.
- Priority: High
- Effort: M
- Impact: High
- Area: DX / reliability
- Files: `lib/api-client.ts`, shared type definitions, route consumers
- Dependencies: stable backend route names.
- Risks: over-automation can hide endpoint-specific behavior.
- Completion criterion: the most-used calls are typed and stay in sync with the backend.
- Instructions for future agents: keep the client explicit enough to remain readable.

## WEB-03 - Add a real frontend smoke test path
- Problem: the current safety net is mostly build and type-check.
- Benefit: better confidence in onboarding, cockpit, and form flows.
- Priority: Medium
- Effort: M
- Impact: High
- Area: test
- Files: `app/**`, `components/**`
- Dependencies: stable seeds and backend availability.
- Risks: brittle tests if the route text changes often.
- Completion criterion: one test can open the app, create or seed a project, and reach the main thread flow.
- Instructions for future agents: keep the first smoke test short and realistic.

## WEB-04 - Tighten the default navigation even further for non-experts
- Problem: advanced sections are progressive, but the app is still broad.
- Benefit: less cognitive overload on first use.
- Priority: Medium
- Effort: M
- Impact: Medium
- Area: UX
- Files: `lib/tabConfig.ts`, `components/project-tab-nav.tsx`, `components/project-home-guide.tsx`
- Dependencies: workflow strip and cockpit summaries.
- Risks: hiding too much can frustrate expert users.
- Completion criterion: first-time users see one obvious path while experts still have access.
- Instructions for future agents: keep expert affordances reachable but secondary.

## WEB-05 - Improve docs portal ergonomics
- Problem: the docs portal is functional, but the sidebar is still a flat registry.
- Benefit: easier onboarding for new users and coding agents.
- Priority: Low
- Effort: S
- Impact: Medium
- Area: documentation / UX
- Files: `app/docs/page.tsx`, `app/docs/[slug]/page.tsx`, `lib/docs.ts`
- Dependencies: docs content structure.
- Risks: duplicating the repository docs in two places.
- Completion criterion: users can find the right manual page faster without leaving the app.
- Instructions for future agents: keep the in-app docs synchronized with the repository docs.

## Note for the Next Coding Agent
1. Read `docs/README_PROJECT.md` and `docs/TECHNICAL_ANALYSIS.md` first.
2. Decide whether the change belongs in a route, a shared component, or `lib/`.
3. Reuse the existing profile and label system instead of introducing a second one.
4. Keep the default experience focused on the main thread flow.
5. Verify behavior with `npm run build` and `npx tsc --noEmit` before expanding scope.
