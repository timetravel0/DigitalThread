# Deployment

## Prerequisites
- Node.js 20+
- a running ThreadLite API backend

## Environment variables observed in the repo
- `NEXT_PUBLIC_API_BASE_URL` - backend base URL used by `apps/web/lib/api-client.ts`

The default fallback in local development is `http://localhost:8000`.

## Local run
```bash
npm install
npm run dev
```

## Production build
```bash
npm run build
npm run start
```

## Quality checks
```bash
npm run lint
npx tsc --noEmit
```

## Deployment notes
- `next.config.mjs` uses `output: "standalone"`, so the app is prepared for container-style deployment.
- The frontend is not useful without a reachable backend API.
- The docs portal assumes the repository markdown files are available in the same checkout.
