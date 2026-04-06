# Security Notes

## Observed security posture
- No authentication or authorization layer is visible in the current API surface.
- CORS is configured through `CORS_ORIGINS` in `app/core/__init__.py` and applied in `app/main.py`.
- Request payloads are validated with Pydantic schemas before they reach the domain services.
- Route handlers explicitly reject route/project mismatches for some create endpoints.

## Main risks
- The API is writable without an auth boundary, so the service should not be exposed publicly as-is.
- Seed and import endpoints can create large amounts of data, so they should be controlled in production.
- The broad route surface increases the chance of accidental exposure if origin and deployment settings are too permissive.

## Handling guidance
- Keep secrets out of the repository and rely on environment variables.
- Use a restrictive `CORS_ORIGINS` list in real deployments.
- Consider auth, rate limiting, and audit logging before externalizing the service.
- Treat import endpoints as trusted-admin or internal tooling unless business rules say otherwise.
