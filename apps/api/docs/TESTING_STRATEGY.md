# Testing Strategy

## Current test layers
- `apps/api/tests/test_api.py` - HTTP smoke tests over the FastAPI routes
- `apps/api/tests/test_federation.py` - federation, registry, and cross-object API tests
- `apps/api/tests/test_services.py` - service-level behavior tests

## What the suite currently protects
- project, requirement, block, and test case workflows
- baseline and change-control flows
- evidence, federation, and configuration-context behavior
- SysML-like and interoperability projection endpoints
- project import and export behavior

## Practical gaps
- there is still room for more end-to-end coverage across the whole thread lifecycle
- some route group combinations are only checked indirectly through service tests
- UI behavior is not covered here and depends on frontend checks

## Recommended command sequence
```bash
python -m pytest -q
python -m compileall .
alembic upgrade head
```

## Guidance for future additions
- add tests next to the route or service family that changed
- prefer realistic payloads over synthetic minimal payloads when the workflow matters
- cover both success and validation failure cases for public routes
