"""Backward-compatible service exports for the DigitalThread API."""

from importlib import import_module
import sys
import types


def _services_legacy_getattr(name: str):
    mapping = {
        "build_impact": ("app.services.impact_views", "build_impact"),
        "build_matrix": ("app.services.impact_views", "build_matrix"),
        "get_global_dashboard": ("app.services.impact_views", "get_global_dashboard"),
        "get_project_dashboard": ("app.services.impact_views", "get_project_dashboard"),
        "get_requirement_detail": ("app.services.impact_views", "get_requirement_detail"),
        "get_component_detail": ("app.services.impact_views", "get_component_detail"),
        "get_test_case_detail": ("app.services.impact_views", "get_test_case_detail"),
        "get_change_request_detail": ("app.services.change_request_service", "get_change_request_detail"),
        "seed_demo": ("app.services.seed_data", "seed_demo"),
        "seed_manufacturing_demo": ("app.services.seed_data", "seed_manufacturing_demo"),
        "seed_personal_demo": ("app.services.seed_data", "seed_personal_demo"),
    }
    if name not in mapping:
        raise AttributeError(name)
    module_name, attr_name = mapping[name]
    return getattr(import_module(module_name), attr_name)


_services_legacy = types.ModuleType("app.services_legacy")
_services_legacy.__getattr__ = _services_legacy_getattr  # type: ignore[attr-defined]
sys.modules.setdefault("app.services_legacy", _services_legacy)

from app.services.project_service import (
    create_project,
    export_project_bundle,
    get_project_dashboard,
    get_project_service,
    get_project_tab_stats,
    list_projects_service,
    list_review_queue,
    update_project,
)
from app.services.requirement_service import (
    approve_requirement,
    create_requirement,
    create_requirement_draft_version,
    list_requirement_history,
    list_requirements,
    reject_requirement,
    send_requirement_back_to_draft,
    submit_requirement_for_review,
    update_requirement,
)
from app.services.block_service import (
    approve_block,
    build_block_tree,
    build_derivation_view,
    build_satisfaction_view,
    build_verification_view,
    create_block,
    create_block_containment,
    create_block_draft_version,
    delete_block_containment,
    get_block_detail,
    list_block_history,
    list_block_containments,
    list_blocks,
    reject_block,
    send_block_back_to_draft,
    submit_block_for_review,
    update_block,
)
from app.services.component_service import (
    create_component,
    list_components,
    update_component,
)
from app.services.test_service import (
    approve_test_case,
    create_test_case,
    create_test_case_draft_version,
    create_test_run,
    list_test_case_history,
    list_test_cases,
    list_test_runs,
    reject_test_case,
    send_test_case_back_to_draft,
    submit_test_case_for_review,
    update_test_case,
)
from app.services.evidence_service import (
    create_operational_evidence,
    create_operational_run,
    create_simulation_evidence,
    create_verification_evidence,
    get_operational_evidence_service,
    get_operational_run_detail,
    get_simulation_evidence_service,
    get_verification_evidence_service,
    list_operational_evidence,
    list_operational_runs,
    list_simulation_evidence,
    list_verification_evidence,
    update_operational_run,
)
from app.services.baseline_service import (
    compare_baselines,
    create_baseline,
    get_baseline_bridge_context,
    get_baseline_detail,
    list_baseline_history,
    list_baselines,
    obsolete_baseline,
    release_baseline,
)
from app.services.change_request_service import (
    approve_change_request,
    close_change_request,
    create_change_impact,
    create_change_request,
    get_change_request_detail,
    list_change_impacts,
    list_change_request_history,
    list_change_requests,
    mark_change_request_implemented,
    reject_change_request,
    reopen_change_request,
    submit_change_request_for_analysis,
    update_change_request,
)
from app.services.federation_service import (
    create_artifact_link,
    create_connector,
    create_external_artifact,
    create_external_artifact_version,
    delete_artifact_link,
    get_connector_service,
    get_external_artifact_service,
    list_artifact_links,
    list_connectors,
    list_external_artifact_versions,
    list_external_artifacts,
    update_connector,
    update_external_artifact,
)
from app.services.configuration_service import (
    compare_baseline_to_configuration_context,
    compare_configuration_contexts,
    create_configuration_context,
    create_configuration_item_mapping,
    delete_configuration_item_mapping,
    get_authoritative_registry_summary,
    get_configuration_context_service,
    list_configuration_context_history,
    list_configuration_contexts,
    list_configuration_item_mappings,
    update_configuration_context,
)
from app.services.registry_service import (
    build_step_ap242_contract,
    build_sysml_mapping_contract,
    resolve_object,
    summarize,
)
from app.services.import_service import import_project_records
from app.services.fmi_service import (
    create_fmi_contract,
    get_fmi_contract_service,
    list_fmi_contracts,
)
from app.services.link_service import (
    create_link,
    create_sysml_relation,
    delete_link,
    delete_sysml_relation,
    list_links,
    list_sysml_relations,
)
from app.services.non_conformity_service import (
    create_non_conformity,
    get_non_conformity_detail,
    list_non_conformities,
    update_non_conformity,
)
from app.impact_service import (
    build_impact,
    build_matrix,
    get_change_request_detail as get_change_request_detail_impact,
    get_component_detail,
    get_global_dashboard,
    get_requirement_detail,
    get_test_case_detail,
)
from app.seed_service import (
    seed_demo,
    seed_manufacturing_demo,
    seed_personal_demo,
)
