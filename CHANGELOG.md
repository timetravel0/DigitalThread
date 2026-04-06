## [Unreleased]

### Refactored
- Decomposed `apps/api/app/services.py` (~334 KB) into domain service modules under `apps/api/app/services/` package.
- Modules created: `_common`, `project_service`, `requirement_service`, `block_service`, `component_service`, `test_service`, `evidence_service`, `baseline_service`, `change_request_service`, `federation_service`, `configuration_service`, `registry_service`, `import_service`, `fmi_service`, `link_service`, `non_conformity_service`.
- Backward compatibility preserved via `services/__init__.py` re-exports.
- No public API or database schema changes.
