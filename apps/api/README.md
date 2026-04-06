# ThreadLite API

## Service Layer Architecture

The backend service layer is split into focused modules under `app/services/`.
`app.services.__init__` re-exports the public API for backward compatibility, so
existing router imports continue to work unchanged.

`_common.py` hosts shared helpers and invariants. Routers should not import it
directly; they should import the public service functions from `app.services`.

- `_common.py` - shared helpers, snapshots, parsing, validation, and registry constants.
- `project_service.py` - project CRUD, project dashboards, tab stats, exports, and the review queue.
- `requirement_service.py` - requirement CRUD and review workflow.
- `block_service.py` - block CRUD, containment, block history, and block views.
- `component_service.py` - component CRUD.
- `test_service.py` - test case CRUD and test runs.
- `evidence_service.py` - verification, simulation, and operational evidence plus operational runs.
- `baseline_service.py` - baseline creation, release, history, comparison, and bridge context.
- `change_request_service.py` - change request workflow and change impacts.
- `federation_service.py` - connectors, external artifacts, artifact versions, and artifact links.
- `configuration_service.py` - configuration contexts, mappings, comparison, and registry summaries.
- `registry_service.py` - object resolution and SysML / STEP contract builders.
- `import_service.py` - JSON and CSV import parsing and ingestion.
- `fmi_service.py` - FMI contract CRUD.
- `link_service.py` - generic links and SysML relations.
- `non_conformity_service.py` - non-conformity CRUD and detail.
- `impact_service.py` - project impact, matrix, dashboard, and detail facade.
- `seed_service.py` - demo seed creation facade.
