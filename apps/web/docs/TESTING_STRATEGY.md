# Testing Strategy

## Current safety net
- `npm run build` catches Next.js and TypeScript integration issues.
- `npm run lint` covers lint-level regressions.
- `npx tsc --noEmit` is a useful extra type safety check because there is no dedicated test runner defined in `package.json`.

## What should be tested more deeply
- project cockpit rendering for empty and populated projects
- profile-based navigation visibility
- create/edit form submissions and validation errors
- docs portal navigation and markdown rendering
- validation cockpit alerts and state transitions

## Practical recommendation
- add a small end-to-end smoke suite before adding many isolated component tests
- prioritize the routes that create, link, approve, and review data
- keep test data close to the seeded demo scenarios so the tests remain readable
