# Architecture

## Backend Service Modules

```
apps/api/app/services/
??? __init__.py
??? _common.py
??? baseline_service.py
??? block_service.py
??? change_request_service.py
??? component_service.py
??? configuration_service.py
??? evidence_service.py
??? federation_service.py
??? fmi_service.py
??? import_service.py
??? link_service.py
??? non_conformity_service.py
??? project_service.py
??? registry_service.py
??? requirement_service.py
??? test_service.py
```

| Module | Domain | Key public functions |
|--------|--------|----------------------|
| `_common.py` | Shared helpers | `_add`, `_touch`, `_snapshot`, `_log_action`, `OBJECT_MODELS`, parsing and validation helpers |
| `project_service.py` | Projects | `create_project`, `update_project`, `get_project_dashboard`, `get_project_tab_stats`, `export_project_bundle`, `list_review_queue` |
| `requirement_service.py` | Requirements | `create_requirement`, `update_requirement`, `create_requirement_draft_version`, `submit_requirement_for_review`, `approve_requirement`, `reject_requirement`, `send_requirement_back_to_draft`, `list_requirement_history`, `list_requirements` |
| `block_service.py` | Blocks | `create_block`, `update_block`, `create_block_draft_version`, `submit_block_for_review`, `approve_block`, `reject_block`, `send_block_back_to_draft`, `list_blocks`, `get_block_detail`, `list_block_history`, `create_block_containment`, `delete_block_containment`, `list_block_containments`, `build_block_tree`, `build_satisfaction_view`, `build_verification_view`, `build_derivation_view` |
| `component_service.py` | Components | `create_component`, `update_component`, `list_components` |
| `test_service.py` | Test Cases | `create_test_case`, `update_test_case`, `create_test_case_draft_version`, `submit_test_case_for_review`, `approve_test_case`, `reject_test_case`, `send_test_case_back_to_draft`, `list_test_case_history`, `list_test_cases`, `create_test_run`, `list_test_runs` |
| `evidence_service.py` | Evidence and Runs | `create_verification_evidence`, `list_verification_evidence`, `get_verification_evidence_service`, `create_simulation_evidence`, `list_simulation_evidence`, `get_simulation_evidence_service`, `create_operational_evidence`, `list_operational_evidence`, `get_operational_evidence_service`, `create_operational_run`, `update_operational_run`, `list_operational_runs`, `get_operational_run_detail` |
| `baseline_service.py` | Baselines | `create_baseline`, `release_baseline`, `obsolete_baseline`, `list_baselines`, `get_baseline_detail`, `list_baseline_history`, `get_baseline_bridge_context`, `compare_baselines` |
| `change_request_service.py` | Change Requests | `create_change_request`, `update_change_request`, `list_change_requests`, `list_change_request_history`, `submit_change_request_for_analysis`, `approve_change_request`, `reject_change_request`, `reopen_change_request`, `mark_change_request_implemented`, `close_change_request`, `create_change_impact`, `list_change_impacts`, `get_change_request_detail` |
| `federation_service.py` | Federation | `create_connector`, `update_connector`, `list_connectors`, `get_connector_service`, `create_external_artifact`, `update_external_artifact`, `list_external_artifacts`, `get_external_artifact_service`, `create_external_artifact_version`, `list_external_artifact_versions`, `create_artifact_link`, `delete_artifact_link`, `list_artifact_links` |
| `configuration_service.py` | Configuration Contexts | `create_configuration_context`, `update_configuration_context`, `list_configuration_contexts`, `get_configuration_context_service`, `create_configuration_item_mapping`, `delete_configuration_item_mapping`, `list_configuration_item_mappings`, `list_configuration_context_history`, `compare_configuration_contexts`, `compare_baseline_to_configuration_context`, `get_authoritative_registry_summary` |
| `registry_service.py` | Registry and Contracts | `resolve_object`, `summarize`, `build_sysml_mapping_contract`, `build_step_ap242_contract` |
| `import_service.py` | Imports | `import_project_records` |
| `fmi_service.py` | FMI | `create_fmi_contract`, `update_fmi_contract`, `list_fmi_contracts`, `get_fmi_contract_service` |
| `link_service.py` | Links | `create_link`, `delete_link`, `list_links`, `create_sysml_relation`, `delete_sysml_relation`, `list_sysml_relations` |
| `non_conformity_service.py` | Non-Conformities | `create_non_conformity`, `update_non_conformity`, `list_non_conformities`, `get_non_conformity_detail` |
| `impact_service.py` | Dashboard and detail facade | `get_global_dashboard`, `get_project_dashboard`, `build_matrix`, `build_impact`, `get_requirement_detail`, `get_component_detail`, `get_test_case_detail`, `get_change_request_detail` |
| `seed_service.py` | Demo seeding facade | `seed_demo`, `seed_manufacturing_demo`, `seed_personal_demo` |

`app.services` remains the compatibility import surface. New code should continue to import public service functions from `app.services`, while the internal modules stay focused on their domains.
