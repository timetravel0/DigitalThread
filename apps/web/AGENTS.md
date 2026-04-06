# AGENTS.md

## Scopo
ThreadLite web application for the Digital Thread cockpit, forms, navigation, traceability views, validation, and documentation portal.

## Identita del progetto
- Nome: ThreadLite Web
- Path root: `apps/web`
- Tipo: frontend application
- Stack principale: Next.js 14, React 18, TypeScript, Tailwind CSS, React Hook Form, Zod

## Cartelle rilevanti
- `app/` - App Router pages and route layouts
- `components/` - UI components, forms, cockpit, docs renderer, traceability views
- `lib/` - API client, labels, tab visibility, project context, docs registry, shared types
- `docs/` - project-specific frontend analysis docs
- `app/docs/` - in-app documentation portal routes

## Cartelle da ignorare
- `node_modules/`
- `.next/`
- `tsconfig.tsbuildinfo`
- `dist/`
- `build/`
- `.git/`

## Convenzioni osservate
- App Router pages compose the UI; most data is fetched server-side in the route component.
- `components/ui.tsx` provides shared shell primitives and layout building blocks.
- `lib/api-client.ts` is the single frontend API gateway to the backend.
- `lib/labels.ts` and `lib/tabConfig.ts` control domain-profile vocabulary and navigation exposure.
- `lib/projectContext.tsx` supplies project-scoped dashboard data, labels, and advanced-mode state.
- Forms use React Hook Form plus Zod.

## Comandi utili
```bash
# installazione
npm install

# avvio locale
npm run dev

# test
npm run build

# lint / type-check
npm run lint
npx tsc --noEmit

# build
npm run build
```

## Guardrail
- Leggi prima `README.md` e the project docs in `docs/`.
- Reuse `api-client`, `labels`, `tabConfig`, and `projectContext` instead of adding parallel state.
- Keep advanced features behind progressive disclosure unless they are truly ready.
- Prefer small, composable UI changes.
- Avoid introducing new dependencies unless there is a clear product reason.

## Riferimenti alla documentazione
- `README.md`
- `docs/README_PROJECT.md`
- `docs/FUNCTIONAL_ANALYSIS.md`
- `docs/TECHNICAL_ANALYSIS.md`
- `docs/DEPLOYMENT.md`
- `docs/SECURITY_NOTES.md`
- `docs/TESTING_STRATEGY.md`
- `docs/IMPROVEMENT_ROADMAP.md`
