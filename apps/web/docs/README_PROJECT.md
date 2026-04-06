# ThreadLite Web Project

## Purpose
ThreadLite Web is the user-facing Digital Thread cockpit. It lets users create projects, author and review thread objects, inspect traceability, browse documentation, and run guided validation flows.

## Identity
- Path root: `apps/web`
- Type: frontend application
- Stack: Next.js 14, React 18, TypeScript, Tailwind CSS, React Hook Form, Zod

## Main responsibilities
- render the dashboard and project cockpit
- provide create/edit/detail pages for thread objects
- expose navigation and progressive disclosure for advanced views
- render the in-app documentation portal
- call the backend API through a central client

## Relevant folders
- `app/` - App Router routes and layouts
- `components/` - UI, forms, cockpit, traceability, docs rendering
- `lib/` - API client, labels, tabs, project context, docs registry, shared types
- `docs/` - frontend-specific analysis and planning docs
- `app/docs/` - built-in documentation portal routes

## Setup and commands
```bash
npm install
npm run dev
npm run build
npm run start
npm run lint
npx tsc --noEmit
```

## Related documents
- `docs/FUNCTIONAL_ANALYSIS.md`
- `docs/TECHNICAL_ANALYSIS.md`
- `docs/DEPLOYMENT.md`
- `docs/SECURITY_NOTES.md`
- `docs/TESTING_STRATEGY.md`
- `docs/IMPROVEMENT_ROADMAP.md`
