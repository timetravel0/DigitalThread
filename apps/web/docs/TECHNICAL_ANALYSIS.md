# Technical Analysis

## Stack
- Next.js 14 App Router in `app/`
- React 18 client and server components
- TypeScript 5.6
- Tailwind CSS with shared design primitives in `components/ui.tsx`
- React Hook Form and Zod for forms
- Lucide icons for UI affordances

## Entrypoints and layout
- `app/layout.tsx` wraps the whole app with the shell and toast provider.
- `components/ui.tsx` provides the shared shell, cards, buttons, inputs, and layout primitives.
- `components/navigation.tsx` renders the sidebar and top bar.
- `app/page.tsx` redirects to the dashboard.

## Main technical modules
- `lib/api-client.ts` is the single HTTP client for backend requests.
- `lib/projectContext.tsx` stores project scope, labels, tab stats, dashboard data, and advanced-mode state.
- `lib/labels.ts` maps domain profiles to the project vocabulary.
- `lib/tabConfig.ts` controls tab visibility and the recommended workflow strip.
- `lib/docs.ts` resolves the markdown docs registry used by the portal.
- `components/markdown-renderer.tsx` renders repository markdown.

## Route structure
- global dashboard and projects list
- project cockpit under `app/projects/[id]/[[...section]]/page.tsx`
- dedicated detail and edit routes for requirements, blocks, components, tests, baselines, change requests, evidence, federation, and configuration contexts
- docs portal under `app/docs/`

## Technical patterns
- most pages fetch data on the server and render with shared components
- project-specific client state lives in `ProjectProvider`
- the project cockpit composes summary cards, workflow cues, navigation tabs, and advanced section views
- forms use RHF + Zod and share common footer/helper components
- markdown docs are read from the repository filesystem at runtime/build time

## Integration points
- the frontend calls the FastAPI backend through `api-client.ts`
- the base API URL is driven by `NEXT_PUBLIC_API_BASE_URL`
- the docs portal uses static path resolution to read repository markdown files
- project pages depend on backend route names and payload shapes remaining stable

## Quality observations
- `app/projects/[id]/[[...section]]/page.tsx` is a very large route component and holds many views in one file
- `api-client.ts` mirrors a broad backend surface with many handwritten wrappers
- the app is operational, but a lot of product logic is encoded in routes and component props rather than in smaller domain adapters
- there is no rich frontend test suite visible in the repository; build, lint, and type-check are the current safety net

## Maintainability notes
- the profile/label system is a useful abstraction and should stay central
- advanced navigation should remain progressive, not duplicated
- direct backend route changes should be reflected in `api-client.ts`, `tabConfig.ts`, and the docs portal registry when relevant
