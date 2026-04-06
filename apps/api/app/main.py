from __future__ import annotations

import json
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlmodel import Session

from app.core import get_settings
from app.db import get_session, init_db
from app.models import (
    ConnectorType,
    ExternalArtifactType,
    FederatedInternalObjectType,
    OperationalEvidenceLinkObjectType,
    Priority,
    RequirementCategory,
    RequirementStatus,
    SimulationEvidenceLinkObjectType,
)
from app.schemas import (
    ArtifactLinkCreate,
    ArtifactLinkRead,
    AuthoritativeRegistrySummary,
    BaselineBridgeContextRead,
    BaselineComparisonResponse,
    BaselineContextComparisonResponse,
    BaselineCreate,
    BaselineDetailRead,
    BaselineRead,
    BlockContainmentCreate,
    BlockContainmentRead,
    BlockCreate,
    BlockRead,
    BlockUpdate,
    ChangeImpactCreate,
    ChangeImpactRead,
    ChangeRequestCreate,
    ChangeRequestDetail,
    ChangeRequestRead,
    ChangeRequestUpdate,
    ComponentDetail,
    ComponentRead,
    ConfigurationContextComparisonResponse,
    ConfigurationContextCreate,
    ConfigurationContextRead,
    ConfigurationContextUpdate,
    ConfigurationItemMappingCreate,
    ConfigurationItemMappingRead,
    ConnectorDefinitionCreate,
    ConnectorDefinitionRead,
    ConnectorDefinitionUpdate,
    ExternalArtifactCreate,
    ExternalArtifactRead,
    ExternalArtifactUpdate,
    ExternalArtifactVersionCreate,
    ExternalArtifactVersionRead,
    FMIContractCreate,
    FMIContractDetail,
    FMIContractRead,
    GlobalDashboard,
    ImpactResponse,
    LinkCreate,
    LinkRead,
    MatrixResponse,
    NonConformityCreate,
    NonConformityDetail,
    NonConformityRead,
    NonConformityUpdate,
    OperationalEvidenceCreate,
    OperationalEvidenceRead,
    OperationalRunCreate,
    OperationalRunDetail,
    OperationalRunRead,
    OperationalRunUpdate,
    ProjectCreate,
    ProjectDashboard,
    ProjectImportCreate,
    ProjectImportResponse,
    ProjectRead,
    ProjectTabStats,
    ProjectUpdate,
    RequirementCreate,
    RequirementDetail,
    RequirementRead,
    RequirementUpdate,
    ReviewQueueResponse,
    RevisionSnapshotRead,
    STEPAP242ContractResponse,
    SimulationEvidenceCreate,
    SimulationEvidenceRead,
    SysMLDerivationResponse,
    SysMLMappingContractResponse,
    SysMLRelationCreate,
    SysMLRelationRead,
    SysMLSatisfactionResponse,
    SysMLTreeResponse,
    SysMLVerificationResponse,
    TestCaseCreate,
    TestCaseDetail,
    TestCaseRead,
    TestCaseUpdate,
    TestRunCreate,
    TestRunRead,
    VerificationEvidenceCreate,
    VerificationEvidenceRead,
    WorkflowActionPayload,
)
from app.services import (
    approve_block,
    approve_change_request,
    approve_requirement,
    approve_test_case,
    build_block_tree,
    build_derivation_view,
    build_satisfaction_view,
    build_step_ap242_contract,
    build_sysml_mapping_contract,
    build_verification_view,
    close_change_request,
    compare_baseline_to_configuration_context,
    compare_baselines,
    compare_configuration_contexts,
    create_artifact_link,
    create_baseline,
    create_block,
    create_block_containment,
    create_block_draft_version,
    create_change_impact,
    create_change_request,
    create_configuration_context,
    create_configuration_item_mapping,
    create_connector,
    create_external_artifact,
    create_external_artifact_version,
    create_fmi_contract,
    create_link,
    create_non_conformity,
    create_operational_evidence,
    create_operational_run,
    create_project,
    create_requirement,
    create_requirement_draft_version,
    create_simulation_evidence,
    create_sysml_relation,
    create_test_case,
    create_test_case_draft_version,
    create_test_run,
    create_verification_evidence,
    delete_artifact_link,
    delete_block_containment,
    delete_configuration_item_mapping,
    delete_link,
    delete_sysml_relation,
    export_project_bundle,
    get_authoritative_registry_summary,
    get_baseline_bridge_context,
    get_baseline_detail,
    get_block_detail,
    get_configuration_context_service,
    get_connector_service,
    get_external_artifact_service,
    get_fmi_contract_service,
    get_non_conformity_detail,
    get_operational_evidence_service,
    get_operational_run_detail,
    get_project_service,
    get_project_tab_stats,
    get_simulation_evidence_service,
    get_verification_evidence_service,
    import_project_records,
    list_artifact_links,
    list_baselines,
    list_block_containments,
    list_block_history,
    list_blocks,
    list_change_impacts,
    list_change_requests,
    list_components,
    list_configuration_contexts,
    list_configuration_item_mappings,
    list_connectors,
    list_external_artifact_versions,
    list_external_artifacts,
    list_fmi_contracts,
    list_links,
    list_non_conformities,
    list_operational_evidence,
    list_operational_runs,
    list_projects_service,
    list_requirement_history,
    list_requirements,
    list_review_queue,
    list_simulation_evidence,
    list_sysml_relations,
    list_test_case_history,
    list_test_cases,
    list_test_runs,
    list_verification_evidence,
    mark_change_request_implemented,
    obsolete_baseline,
    reject_block,
    reject_change_request,
    reject_requirement,
    reject_test_case,
    release_baseline,
    reopen_change_request,
    send_block_back_to_draft,
    send_requirement_back_to_draft,
    send_test_case_back_to_draft,
    submit_block_for_review,
    submit_change_request_for_analysis,
    submit_requirement_for_review,
    submit_test_case_for_review,
    update_block,
    update_change_request,
    update_configuration_context,
    update_connector,
    update_external_artifact,
    update_non_conformity,
    update_operational_run,
    update_project,
    update_requirement,
    update_test_case,
)
from app.impact_service import (
    build_impact,
    build_matrix,
    get_change_request_detail,
    get_component_detail,
    get_global_dashboard,
    get_project_dashboard,
    get_requirement_detail,
    get_test_case_detail,
)
from app.seed_service import seed_demo, seed_manufacturing_demo, seed_personal_demo

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def db(session: Session = Depends(get_session)) -> Session:
    return session


def api_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/projects", response_model=list[ProjectRead])
def list_projects_endpoint(session: Session = Depends(db)):
    return list_projects_service(session)


@app.post("/api/projects", response_model=ProjectRead, status_code=201)
def create_project_endpoint(payload: ProjectCreate, session: Session = Depends(db)):
    try:
        return create_project(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        return get_project_service(session, project_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/projects/{project_id}", response_model=ProjectRead)
@app.patch("/api/projects/{project_id}", response_model=ProjectRead)
def update_project_endpoint(project_id: UUID, payload: ProjectUpdate, session: Session = Depends(db)):
    try:
        return update_project(session, project_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/export")
def export_project_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        bundle = export_project_bundle(session, project_id)
        filename = f"threadlite-{bundle['project']['code']}.json"
        return Response(
            content=json.dumps(bundle, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/dashboard", response_model=GlobalDashboard)
def dashboard_endpoint(session: Session = Depends(db)):
    return get_global_dashboard(session)


@app.get("/api/projects/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        return get_project_dashboard(session, project_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/tab-stats", response_model=ProjectTabStats)
def project_tab_stats_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        return get_project_tab_stats(session, project_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/authoritative-registry-summary", response_model=AuthoritativeRegistrySummary)
def authoritative_registry_summary_endpoint(project_id: UUID, session: Session = Depends(db)):
    return get_authoritative_registry_summary(session, project_id)


@app.get("/api/projects/{project_id}/connectors", response_model=list[ConnectorDefinitionRead])
def list_connectors_endpoint(project_id: UUID, session: Session = Depends(db)):
    return list_connectors(session, project_id)


@app.post("/api/projects/{project_id}/connectors", response_model=ConnectorDefinitionRead, status_code=201)
def create_connector_endpoint(project_id: UUID, payload: ConnectorDefinitionCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Connector project_id must match the route project_id")
        return create_connector(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/connectors/{obj_id}", response_model=dict)
def connector_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_connector_service(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/connectors/{obj_id}", response_model=ConnectorDefinitionRead)
def update_connector_endpoint(obj_id: UUID, payload: ConnectorDefinitionUpdate, session: Session = Depends(db)):
    try:
        return update_connector(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/external-artifacts", response_model=list[ExternalArtifactRead])
def list_external_artifacts_endpoint(
    project_id: UUID,
    connector_definition_id: UUID | None = None,
    connector_type: ConnectorType | None = None,
    artifact_type: ExternalArtifactType | None = None,
    session: Session = Depends(db),
):
    return list_external_artifacts(
        session,
        project_id,
        connector_definition_id=connector_definition_id,
        connector_type=connector_type,
        artifact_type=artifact_type,
    )


@app.post("/api/projects/{project_id}/external-artifacts", response_model=ExternalArtifactRead, status_code=201)
def create_external_artifact_endpoint(project_id: UUID, payload: ExternalArtifactCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("External artifact project_id must match the route project_id")
        return create_external_artifact(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/external-artifacts/{obj_id}", response_model=dict)
def external_artifact_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_external_artifact_service(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/external-artifacts/{obj_id}", response_model=ExternalArtifactRead)
def update_external_artifact_endpoint(obj_id: UUID, payload: ExternalArtifactUpdate, session: Session = Depends(db)):
    try:
        return update_external_artifact(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/external-artifacts/{obj_id}/versions", response_model=list[ExternalArtifactVersionRead])
def list_external_artifact_versions_endpoint(obj_id: UUID, session: Session = Depends(db)):
    return list_external_artifact_versions(session, obj_id)


@app.post("/api/external-artifacts/{obj_id}/versions", response_model=ExternalArtifactVersionRead, status_code=201)
def create_external_artifact_version_endpoint(obj_id: UUID, payload: ExternalArtifactVersionCreate, session: Session = Depends(db)):
    try:
        return create_external_artifact_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/artifact-links", response_model=list[ArtifactLinkRead])
def list_artifact_links_endpoint(
    project_id: UUID,
    internal_object_type: FederatedInternalObjectType | None = None,
    internal_object_id: UUID | None = None,
    external_artifact_id: UUID | None = None,
    session: Session = Depends(db),
):
    return list_artifact_links(
        session,
        project_id,
        internal_object_type=internal_object_type,
        internal_object_id=internal_object_id,
        external_artifact_id=external_artifact_id,
    )


@app.post("/api/projects/{project_id}/artifact-links", response_model=ArtifactLinkRead, status_code=201)
def create_artifact_link_endpoint(project_id: UUID, payload: ArtifactLinkCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Artifact link project_id must match the route project_id")
        return create_artifact_link(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/artifact-links/{link_id}", status_code=204)
def delete_artifact_link_endpoint(link_id: UUID, session: Session = Depends(db)):
    try:
        delete_artifact_link(session, link_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/configuration-contexts", response_model=list[ConfigurationContextRead])
def list_configuration_contexts_endpoint(project_id: UUID, session: Session = Depends(db)):
    return list_configuration_contexts(session, project_id)


@app.post("/api/projects/{project_id}/configuration-contexts", response_model=ConfigurationContextRead, status_code=201)
def create_configuration_context_endpoint(project_id: UUID, payload: ConfigurationContextCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Configuration context project_id must match the route project_id")
        return create_configuration_context(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/configuration-contexts/{obj_id}", response_model=dict)
def configuration_context_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_configuration_context_service(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/configuration-contexts/{obj_id}", response_model=ConfigurationContextRead)
def update_configuration_context_endpoint(obj_id: UUID, payload: ConfigurationContextUpdate, session: Session = Depends(db)):
    try:
        return update_configuration_context(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/configuration-contexts/{obj_id}/items", response_model=list[ConfigurationItemMappingRead])
def list_configuration_item_mappings_endpoint(obj_id: UUID, session: Session = Depends(db)):
    return list_configuration_item_mappings(session, obj_id)


@app.post("/api/configuration-contexts/{obj_id}/items", response_model=ConfigurationItemMappingRead, status_code=201)
def create_configuration_item_mapping_endpoint(obj_id: UUID, payload: ConfigurationItemMappingCreate, session: Session = Depends(db)):
    try:
        return create_configuration_item_mapping(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/configuration-item-mappings/{mapping_id}", status_code=204)
def delete_configuration_item_mapping_endpoint(mapping_id: UUID, session: Session = Depends(db)):
    try:
        delete_configuration_item_mapping(session, mapping_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/configuration-contexts/{obj_id}/resolved-view", response_model=dict)
def configuration_context_resolved_view_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_configuration_context_service(session, obj_id)["resolved_view"]
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/configuration-contexts/{obj_id}/compare/{other_id}", response_model=ConfigurationContextComparisonResponse)
def compare_configuration_contexts_endpoint(obj_id: UUID, other_id: UUID, session: Session = Depends(db)):
    try:
        return compare_configuration_contexts(session, obj_id, other_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements", response_model=list[RequirementRead])
def list_requirements_endpoint(
    project_id: UUID = Query(...),
    status: RequirementStatus | None = None,
    category: RequirementCategory | None = None,
    priority: Priority | None = None,
    session: Session = Depends(db),
):
    return list_requirements(session, project_id, status=status, category=category, priority=priority)


@app.post("/api/requirements", response_model=RequirementRead, status_code=201)
def create_requirement_endpoint(payload: RequirementCreate, session: Session = Depends(db)):
    try:
        return create_requirement(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements/{obj_id}", response_model=RequirementDetail)
def requirement_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_requirement_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/requirements/{obj_id}", response_model=RequirementRead)
def patch_requirement_endpoint(obj_id: UUID, payload: RequirementUpdate, session: Session = Depends(db)):
    try:
        return update_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/submit-review", response_model=RequirementRead)
def submit_requirement_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_requirement_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/approve", response_model=RequirementRead)
def approve_requirement_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/reject", response_model=RequirementRead)
def reject_requirement_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/send-draft", response_model=RequirementRead)
def requirement_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_requirement_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/create-draft-version", response_model=RequirementRead)
def requirement_create_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_requirement_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def requirement_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_requirement_history(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks", response_model=list[BlockRead])
def list_blocks_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_blocks(session, project_id)


@app.post("/api/blocks", response_model=BlockRead, status_code=201)
def create_block_endpoint(payload: BlockCreate, session: Session = Depends(db)):
    try:
        return create_block(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks/{obj_id}", response_model=dict)
def block_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_block_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/blocks/{obj_id}", response_model=BlockRead)
def patch_block_endpoint(obj_id: UUID, payload: BlockUpdate, session: Session = Depends(db)):
    try:
        return update_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/submit-review", response_model=BlockRead)
def submit_block_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_block_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/approve", response_model=BlockRead)
def approve_block_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/reject", response_model=BlockRead)
def reject_block_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/send-draft", response_model=BlockRead)
def block_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_block_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/create-draft-version", response_model=BlockRead)
def block_create_draft_version_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_block_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def block_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_block_history(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/components", response_model=list[ComponentRead])
def list_components_endpoint(project_id: UUID, session: Session = Depends(db)):
    return list_components(session, project_id)


@app.get("/api/components/{obj_id}", response_model=ComponentDetail)
def component_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_component_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases", response_model=list[TestCaseRead])
def list_test_cases_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_test_cases(session, project_id)


@app.post("/api/test-cases", response_model=TestCaseRead, status_code=201)
def create_test_case_endpoint(payload: TestCaseCreate, session: Session = Depends(db)):
    try:
        return create_test_case(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases/{obj_id}", response_model=TestCaseDetail)
def test_case_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_test_case_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/test-cases/{obj_id}", response_model=TestCaseRead)
def patch_test_case_endpoint(obj_id: UUID, payload: TestCaseUpdate, session: Session = Depends(db)):
    try:
        return update_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/submit-review", response_model=TestCaseRead)
def submit_test_case_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_test_case_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/approve", response_model=TestCaseRead)
def approve_test_case_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/reject", response_model=TestCaseRead)
def reject_test_case_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/send-draft", response_model=TestCaseRead)
def test_case_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_test_case_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/create-draft-version", response_model=TestCaseRead)
def test_case_create_draft_version_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_test_case_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/verification-evidence", response_model=list[VerificationEvidenceRead])
def list_verification_evidence_endpoint(
    project_id: UUID,
    internal_object_type: FederatedInternalObjectType | None = None,
    internal_object_id: UUID | None = None,
    session: Session = Depends(db),
):
    return list_verification_evidence(
        session,
        project_id,
        internal_object_type=internal_object_type,
        internal_object_id=internal_object_id,
    )


@app.post("/api/projects/{project_id}/verification-evidence", response_model=VerificationEvidenceRead, status_code=201)
def create_verification_evidence_endpoint(project_id: UUID, payload: VerificationEvidenceCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Verification evidence project_id must match the route project_id")
        return create_verification_evidence(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/verification-evidence/{evidence_id}", response_model=VerificationEvidenceRead)
def verification_evidence_detail_endpoint(evidence_id: UUID, session: Session = Depends(db)):
    try:
        return get_verification_evidence_service(session, evidence_id)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/projects/{project_id}/imports", response_model=ProjectImportResponse, status_code=201)
def import_project_records_endpoint(project_id: UUID, payload: ProjectImportCreate, session: Session = Depends(db)):
    try:
        return import_project_records(session, project_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/simulation-evidence", response_model=list[SimulationEvidenceRead])
def list_simulation_evidence_endpoint(
    project_id: UUID,
    internal_object_type: SimulationEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
    session: Session = Depends(db),
):
    return list_simulation_evidence(
        session,
        project_id,
        internal_object_type=internal_object_type,
        internal_object_id=internal_object_id,
    )


@app.get("/api/projects/{project_id}/fmi-contracts", response_model=list[FMIContractRead])
def list_fmi_contracts_endpoint(project_id: UUID, session: Session = Depends(db)):
    return list_fmi_contracts(session, project_id)


@app.post("/api/projects/{project_id}/fmi-contracts", response_model=FMIContractRead, status_code=201)
def create_fmi_contract_endpoint(project_id: UUID, payload: FMIContractCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("FMI contract project_id must match the route project_id")
        return create_fmi_contract(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/fmi-contracts/{contract_id}", response_model=FMIContractDetail)
def fmi_contract_detail_endpoint(contract_id: UUID, session: Session = Depends(db)):
    try:
        return get_fmi_contract_service(session, contract_id)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/projects/{project_id}/simulation-evidence", response_model=SimulationEvidenceRead, status_code=201)
def create_simulation_evidence_endpoint(project_id: UUID, payload: SimulationEvidenceCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Simulation evidence project_id must match the route project_id")
        return create_simulation_evidence(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/simulation-evidence/{evidence_id}", response_model=SimulationEvidenceRead)
def simulation_evidence_detail_endpoint(evidence_id: UUID, session: Session = Depends(db)):
    try:
        return get_simulation_evidence_service(session, evidence_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/operational-evidence", response_model=list[OperationalEvidenceRead])
def list_operational_evidence_endpoint(
    project_id: UUID,
    internal_object_type: OperationalEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
    session: Session = Depends(db),
):
    return list_operational_evidence(
        session,
        project_id,
        internal_object_type=internal_object_type,
        internal_object_id=internal_object_id,
    )


@app.post("/api/projects/{project_id}/operational-evidence", response_model=OperationalEvidenceRead, status_code=201)
def create_operational_evidence_endpoint(project_id: UUID, payload: OperationalEvidenceCreate, session: Session = Depends(db)):
    try:
        if payload.project_id != project_id:
            raise ValueError("Operational evidence project_id must match the route project_id")
        return create_operational_evidence(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/operational-evidence/{evidence_id}", response_model=OperationalEvidenceRead)
def operational_evidence_detail_endpoint(evidence_id: UUID, session: Session = Depends(db)):
    try:
        return get_operational_evidence_service(session, evidence_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def test_case_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_test_case_history(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-runs", response_model=list[TestRunRead])
def list_test_runs_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_test_runs(session, project_id)


@app.post("/api/test-runs", response_model=TestRunRead, status_code=201)
def create_test_run_endpoint(payload: TestRunCreate, session: Session = Depends(db)):
    try:
        return create_test_run(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/operational-runs", response_model=list[OperationalRunRead])
def list_operational_runs_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_operational_runs(session, project_id)


@app.post("/api/operational-runs", response_model=OperationalRunRead, status_code=201)
def create_operational_run_endpoint(payload: OperationalRunCreate, session: Session = Depends(db)):
    try:
        return create_operational_run(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/operational-runs/{obj_id}", response_model=OperationalRunDetail)
def operational_run_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_operational_run_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/operational-runs/{obj_id}", response_model=OperationalRunRead)
def update_operational_run_endpoint(obj_id: UUID, payload: OperationalRunUpdate, session: Session = Depends(db)):
    try:
        return update_operational_run(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines", response_model=list[BaselineRead])
def list_baselines_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_baselines(session, project_id)


@app.post("/api/baselines", status_code=201)
def create_baseline_endpoint(payload: BaselineCreate, session: Session = Depends(db)):
    try:
        baseline, items = create_baseline(session, payload)
        return {"baseline": baseline, "items": items}
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/baselines/{obj_id}/release", response_model=BaselineRead)
def release_baseline_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return release_baseline(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/baselines/{obj_id}/obsolete", response_model=BaselineRead)
def obsolete_baseline_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return obsolete_baseline(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines/{obj_id}", response_model=BaselineDetailRead)
def baseline_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_baseline_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines/{obj_id}/compare/{context_id}", response_model=BaselineContextComparisonResponse)
def baseline_compare_endpoint(obj_id: UUID, context_id: UUID, session: Session = Depends(db)):
    try:
        return compare_baseline_to_configuration_context(session, obj_id, context_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines/{obj_id}/bridge-context", response_model=BaselineBridgeContextRead)
def baseline_bridge_context_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_baseline_bridge_context(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines/{obj_id}/compare-baseline/{other_id}", response_model=BaselineComparisonResponse)
def baseline_compare_baseline_endpoint(obj_id: UUID, other_id: UUID, session: Session = Depends(db)):
    try:
        return compare_baselines(session, obj_id, other_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-requests", response_model=list[ChangeRequestRead])
def list_change_requests_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_change_requests(session, project_id)


@app.get("/api/projects/{project_id}/non-conformities", response_model=list[NonConformityRead])
def list_non_conformities_endpoint(project_id: UUID, session: Session = Depends(db)):
    return list_non_conformities(session, project_id)


@app.post("/api/non-conformities", response_model=NonConformityRead, status_code=201)
def create_non_conformity_endpoint(payload: NonConformityCreate, session: Session = Depends(db)):
    try:
        return create_non_conformity(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/non-conformities/{obj_id}", response_model=NonConformityDetail)
def non_conformity_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_non_conformity_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/non-conformities/{obj_id}", response_model=NonConformityRead)
def update_non_conformity_endpoint(obj_id: UUID, payload: NonConformityUpdate, session: Session = Depends(db)):
    try:
        return update_non_conformity(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests", response_model=ChangeRequestRead, status_code=201)
def create_change_request_endpoint(payload: ChangeRequestCreate, session: Session = Depends(db)):
    try:
        return create_change_request(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-requests/{obj_id}", response_model=ChangeRequestDetail)
def change_request_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_change_request_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/change-requests/{obj_id}", response_model=ChangeRequestRead)
def update_change_request_endpoint(obj_id: UUID, payload: ChangeRequestUpdate, session: Session = Depends(db)):
    try:
        return update_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/submit-analysis", response_model=ChangeRequestRead)
def submit_change_request_analysis_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_change_request_for_analysis(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/approve", response_model=ChangeRequestRead)
def approve_change_request_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/reject", response_model=ChangeRequestRead)
def reject_change_request_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/implement", response_model=ChangeRequestRead)
def implement_change_request_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return mark_change_request_implemented(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/close", response_model=ChangeRequestRead)
def close_change_request_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return close_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/change-requests/{obj_id}/reopen", response_model=ChangeRequestRead)
def reopen_change_request_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reopen_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-impacts", response_model=list[ChangeImpactRead])
def list_change_impacts_endpoint(change_request_id: UUID = Query(...), session: Session = Depends(db)):
    return list_change_impacts(session, change_request_id)


@app.post("/api/change-impacts", response_model=ChangeImpactRead, status_code=201)
def create_change_impact_endpoint(payload: ChangeImpactCreate, session: Session = Depends(db)):
    try:
        return create_change_impact(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/links", response_model=list[LinkRead])
def list_links_endpoint(project_id: UUID = Query(...), object_type: str | None = None, object_id: UUID | None = None, session: Session = Depends(db)):
    return list_links(session, project_id, object_type=object_type, object_id=object_id)


@app.post("/api/links", response_model=LinkRead, status_code=201)
def create_link_endpoint(payload: LinkCreate, session: Session = Depends(db)):
    try:
        return create_link(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/links/{link_id}", status_code=204)
def delete_link_endpoint(link_id: UUID, session: Session = Depends(db)):
    try:
        delete_link(session, link_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/sysml-relations", response_model=list[SysMLRelationRead])
def list_sysml_relations_endpoint(project_id: UUID = Query(...), object_type: str | None = None, object_id: UUID | None = None, session: Session = Depends(db)):
    return list_sysml_relations(session, project_id, object_type=object_type, object_id=object_id)


@app.post("/api/sysml-relations", response_model=SysMLRelationRead, status_code=201)
def create_sysml_relation_endpoint(payload: SysMLRelationCreate, session: Session = Depends(db)):
    try:
        return create_sysml_relation(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/sysml-relations/{relation_id}", status_code=204)
def delete_sysml_relation_endpoint(relation_id: UUID, session: Session = Depends(db)):
    try:
        delete_sysml_relation(session, relation_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/block-containments", response_model=list[BlockContainmentRead])
def list_block_containments_endpoint(project_id: UUID = Query(...), object_id: UUID | None = None, session: Session = Depends(db)):
    return list_block_containments(session, project_id, obj_id=object_id)


@app.post("/api/block-containments", response_model=BlockContainmentRead, status_code=201)
def create_block_containment_endpoint(payload: BlockContainmentCreate, session: Session = Depends(db)):
    try:
        return create_block_containment(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/block-containments/{containment_id}", status_code=204)
def delete_block_containment_endpoint(containment_id: UUID, session: Session = Depends(db)):
    try:
        delete_block_containment(session, containment_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/review-queue", response_model=ReviewQueueResponse)
def review_queue_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_review_queue(session, project_id)


@app.get("/api/projects/{project_id}/sysml/block-tree", response_model=SysMLTreeResponse)
def block_tree_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_block_tree(session, project_id)


@app.get("/api/projects/{project_id}/sysml/satisfaction", response_model=SysMLSatisfactionResponse)
def satisfaction_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_satisfaction_view(session, project_id)


@app.get("/api/projects/{project_id}/sysml/verification", response_model=SysMLVerificationResponse)
def verification_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_verification_view(session, project_id)


@app.get("/api/projects/{project_id}/sysml/derivations", response_model=SysMLDerivationResponse)
def derivations_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_derivation_view(session, project_id)


@app.get("/api/projects/{project_id}/sysml/mapping-contract", response_model=SysMLMappingContractResponse)
def mapping_contract_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_sysml_mapping_contract(session, project_id)


@app.get("/api/projects/{project_id}/step-ap242-contract", response_model=STEPAP242ContractResponse)
def step_ap242_contract_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_step_ap242_contract(session, project_id)


@app.get("/api/projects/{project_id}/matrix", response_model=MatrixResponse)
def matrix_endpoint(project_id: UUID, mode: str = Query("components"), status: RequirementStatus | None = None, category: RequirementCategory | None = None, session: Session = Depends(db)):
    return build_matrix(session, project_id, mode=mode, status=status, category=category)


@app.get("/api/projects/{project_id}/impact/{object_type}/{object_id}", response_model=ImpactResponse)
def impact_endpoint(project_id: UUID, object_type: str, object_id: UUID, session: Session = Depends(db)):
    return build_impact(session, project_id, object_type, object_id)


@app.post("/api/seed/demo")
def seed_demo_endpoint(session: Session = Depends(db)):
    try:
        return seed_demo(session)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/seed/manufacturing-demo")
def seed_manufacturing_demo_endpoint(session: Session = Depends(db)):
    try:
        return seed_manufacturing_demo(session)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/seed/personal-demo")
def seed_personal_demo_endpoint(session: Session = Depends(db)):
    try:
        return seed_personal_demo(session)
    except Exception as exc:
        raise api_error(exc)
