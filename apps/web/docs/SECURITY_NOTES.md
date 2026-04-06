# Security Notes

## Observed security posture
- There is no frontend authentication or authorization layer visible in the app.
- The UI trusts the backend API for data integrity and workflow enforcement.
- The docs renderer uses `dangerouslySetInnerHTML`, but it only renders repository markdown content, not arbitrary user content.
- External links in markdown are opened in a new tab with `rel="noreferrer"`.

## Main risks
- The frontend cannot protect sensitive data on its own if the backend is exposed broadly.
- A misconfigured `NEXT_PUBLIC_API_BASE_URL` can point the client at the wrong API.
- Large forms and rich detail pages expose a broad surface for validation mistakes if backend schemas drift.

## Handling guidance
- Keep the backend origin and CORS settings aligned with the deployed frontend origin.
- Treat the app as a trusted internal tool until auth is introduced.
- Keep docs content repository-owned and reviewed.
- Preserve explicit validation and error reporting in forms so users do not guess at hidden rules.
