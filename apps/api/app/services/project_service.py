"""Project Service service layer for the DigitalThread API."""

from __future__ import annotations

from collections import defaultdict, deque
from collections import Counter
import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlmodel import Session

from app.models import (
    AbstractionLevel,
    ApprovalActionLog,
    ArtifactLink,
    ArtifactLinkRelationType,
    Baseline,
    BaselineItem,
    BaselineObjectType,
    BaselineStatus,
    Block,
    BlockContainment,
    BlockContainmentRelationType,
    BlockKind,
    BlockStatus,
    ChangeImpact,
    ChangeRequest,
    ChangeRequestStatus,
    Component,
    ComponentStatus,
    ComponentType,
    ConfigurationContext,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConfigurationItemMapping,
    ConnectorDefinition,
    ConnectorType,
    ExternalArtifact,
    ExternalArtifactStatus,
    ExternalArtifactType,
    ExternalArtifactVersion,
    FMIContract,
    FederatedInternalObjectType,
    ImpactLevel,
    Link,
    LinkObjectType,
    NonConformity,
    NonConformityDisposition,
    NonConformityStatus,
    OperationalEvidence,
    OperationalEvidenceLink,
    OperationalEvidenceLinkObjectType,
    OperationalEvidenceQualityStatus,
    OperationalEvidenceSourceType,
    OperationalOutcome,
    OperationalRun,
    Priority,
    Project,
    ProjectStatus,
    RelationType,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    RequirementVerificationStatus,
    RevisionSnapshot,
    Severity,
    SimulationEvidence,
    SimulationEvidenceLink,
    SimulationEvidenceLinkObjectType,
    SimulationEvidenceResult,
    SysMLObjectType,
    SysMLRelation,
    SysMLRelationType,
    TestCase,
    TestCaseStatus,
    TestMethod,
    TestRun,
    TestRunResult,
    VerificationEvidence,
    VerificationEvidenceLink,
    VerificationEvidenceType,
    VerificationMethod,
    utcnow,
)
from app.schemas import (
    ApprovalActionLogRead,
    ArtifactLinkCreate,
    ArtifactLinkRead,
    AuthoritativeRegistrySummary,
    BaselineBridgeContextRead,
    BaselineComparisonResponse,
    BaselineContextComparisonResponse,
    BaselineCreate,
    BaselineDetailRead,
    BaselineItemRead,
    BaselineRead,
    BlockContainmentCreate,
    BlockContainmentRead,
    BlockCreate,
    BlockRead,
    BlockTreeNode,
    BlockUpdate,
    ChangeImpactCreate,
    ChangeImpactRead,
    ChangeRequestCreate,
    ChangeRequestDetail,
    ChangeRequestRead,
    ChangeRequestUpdate,
    ComponentCreate,
    ComponentDetail,
    ComponentRead,
    ComponentUpdate,
    ConfigurationContextComparisonChange,
    ConfigurationContextComparisonEntry,
    ConfigurationContextComparisonGroup,
    ConfigurationContextComparisonResponse,
    ConfigurationContextComparisonSummary,
    ConfigurationContextCreate,
    ConfigurationContextRead,
    ConfigurationContextUpdate,
    ConfigurationItemMappingCreate,
    ConfigurationItemMappingRead,
    ConnectorDefinitionCreate,
    ConnectorDefinitionRead,
    ConnectorDefinitionUpdate,
    DashboardKpis,
    DerivationRow,
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
    MatrixCell,
    MatrixColumn,
    MatrixResponse,
    MatrixRow,
    NonConformityCreate,
    NonConformityDetail,
    NonConformityRead,
    NonConformityUpdate,
    ObjectSummary,
    OperationalEvidenceCreate,
    OperationalEvidenceLinkRead,
    OperationalEvidenceRead,
    OperationalRunCreate,
    OperationalRunDetail,
    OperationalRunRead,
    OperationalRunUpdate,
    ProjectCreate,
    ProjectDashboard,
    ProjectImportCreate,
    ProjectImportResponse,
    ProjectImportSummary,
    ProjectRead,
    ProjectTabStats,
    ProjectUpdate,
    RequirementCreate,
    RequirementDetail,
    RequirementRead,
    RequirementUpdate,
    RequirementVerificationEvaluation,
    ReviewQueueItem,
    ReviewQueueResponse,
    RevisionSnapshotRead,
    SatisfactionRow,
    STEPAP242ContractResponse,
    STEPAP242IdentifierRow,
    STEPAP242PartRow,
    STEPAP242RelationRow,
    STEPAP242Summary,
    SimulationEvidenceCreate,
    SimulationEvidenceLinkRead,
    SimulationEvidenceRead,
    SysMLBlockMappingRow,
    SysMLDerivationResponse,
    SysMLMappingContractResponse,
    SysMLMappingRelationRow,
    SysMLMappingSummary,
    SysMLRelationCreate,
    SysMLRelationRead,
    SysMLRequirementMappingRow,
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
    VerificationRow,
    VerificationStatusBreakdown,
    WorkflowActionPayload,
)

from app.services._common import (
    _add,
    _touch,
    _get,
    _read,
    _items,
    _first_item,
    _normalize_import_row,
    _parse_import_json,
    _parse_import_csv,
    _parse_import_rows,
    _parse_import_json_value,
    _parse_import_datetime,
    _parse_import_uuid,
    _parse_import_uuid_list,
    _infer_import_record_type,
    _status_value,
    _utc_datetime,
    _collect_text_tokens,
    _verification_signal_from_text,
    _verification_signal_from_evidence,
    _simulation_signal_from_evidence,
    _operational_evidence_signal_from_record,
    _threshold_violations,
    _verification_status_breakdown,
    _impact_node_key,
    _impact_context_internal_ids,
    _compute_snapshot_hash,
    _snapshot,
    _log_action,
    _commit,
    _editable,
    _validate_internal_object,
    _validate_external_artifact,
    _validate_external_artifact_version,
    _resolve_external_artifact_version_for_project,
    _validate_fmi_contract,
    _ensure_configuration_context_mutable,
    _artifact_read,
    _fmi_contract_read,
    _connector_read,
    _resolve_artifact_link_internal_label,
    _resolve_artifact_link_external_label,
    _validate_configuration_mapping,
    _configuration_context_comparison_entry,
    _baseline_comparison_entry,
    _compare_configuration_entry_groups,
    _sysml_mapping_semantics,
    _step_ap242_semantics,
    _related_baselines_for_configuration_context,
    _released_baselines_for_object,
    _ensure_change_request_for_released_baseline,
    _decision_history,
    _latest_test_run,
    _evaluate_requirement_verification,
    _verification_evidence_read,
    _validate_verification_evidence_link,
    _simulation_evidence_read,
    _validate_simulation_evidence_link,
    _operational_evidence_read,
    _validate_operational_evidence_link,
    _validate_sysml_relation_pattern,
    _seed_profile_demo,
    _seed_manufacturing_demo_details,
    _seed_personal_demo_details
)
from app.services.requirement_service import list_requirements
from app.services.test_service import list_test_runs
from app.services.change_request_service import list_change_requests
from app.services.link_service import list_links
from app.services.federation_service import list_connectors, list_external_artifacts
from app.services.configuration_service import list_configuration_contexts, list_configuration_item_mappings, get_authoritative_registry_summary
from app.services.baseline_service import list_baselines
from app.services.evidence_service import list_verification_evidence, list_simulation_evidence, list_operational_evidence
from app.services.fmi_service import list_fmi_contracts
from app.services.component_service import list_components

def list_projects_service(session: Session) -> list[ProjectRead]:
    return [ProjectRead.model_validate(item) for item in _items(session.exec(select(Project).order_by(Project.code)))]

def get_project_service(session: Session, project_id: UUID) -> ProjectRead:
    item = _get(session, Project, project_id)
    if item is None:
        raise LookupError("Project not found")
    return _read(ProjectRead, item)

def create_project(session: Session, payload: ProjectCreate) -> ProjectRead:
    item = Project.model_validate(payload)
    if getattr(item, "domain_profile", "engineering") != "custom":
        item.label_overrides = None
    return _read(ProjectRead, _add(session, item))

def update_project(session: Session, project_id: UUID, payload: ProjectUpdate) -> ProjectRead:
    item = _get(session, Project, project_id)
    if item is None:
        raise LookupError("Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    if getattr(item, "domain_profile", "engineering") != "custom":
        item.label_overrides = None
    _touch(item)
    return _read(ProjectRead, _add(session, item))

def get_project_dashboard(session: Session, project_id: UUID) -> ProjectDashboard:
    project = get_project_service(session, project_id)
    requirements = _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))
    links = _items(session.exec(select(Link).where(Link.project_id == project_id)))
    test_runs = list_test_runs(session, project_id)
    change_requests = list_change_requests(session, project_id)
    verification_breakdown = _verification_status_breakdown(session, requirements)

    req_components = req_tests = req_risk = 0
    for req in requirements:
        alloc = [l for l in links if l.source_type == LinkObjectType.requirement and l.source_id == req.id and l.relation_type == RelationType.allocated_to and l.target_type == LinkObjectType.component]
        if alloc:
            req_components += 1
        evaluation = _evaluate_requirement_verification(session, req)
        if evaluation.status != RequirementVerificationStatus.not_covered:
            req_tests += 1
        if evaluation.status in {RequirementVerificationStatus.at_risk, RequirementVerificationStatus.failed}:
            req_risk += 1

    return ProjectDashboard(
        project=project,
        kpis=DashboardKpis(
            total_requirements=len(requirements),
            requirements_with_allocated_components=req_components,
            requirements_with_verifying_tests=req_tests,
            requirements_at_risk=req_risk,
            failed_tests_last_30_days=len([r for r in test_runs if r.result == TestRunResult.failed and r.execution_date >= date.today() - timedelta(days=30)]),
            open_change_requests=len([cr for cr in change_requests if cr.status == ChangeRequestStatus.open]),
        ),
        verification_status_breakdown=verification_breakdown,
        recent_test_runs=test_runs[:5],
        recent_changes=change_requests[:5],
        recent_links=list_links(session, project_id)[:5],
    )

def get_project_tab_stats(session: Session, project_id: UUID) -> ProjectTabStats:
    requirements = _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))
    blocks = _items(session.exec(select(Block).where(Block.project_id == project_id)))
    tests = _items(session.exec(select(TestCase).where(TestCase.project_id == project_id)))
    baselines = _items(session.exec(select(Baseline).where(Baseline.project_id == project_id)))
    change_requests = _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))
    non_conformities = _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id)))
    simulation_evidence = _items(session.exec(select(SimulationEvidence).where(SimulationEvidence.project_id == project_id)))
    operational_evidence = _items(session.exec(select(OperationalEvidence).where(OperationalEvidence.project_id == project_id)))
    operational_runs = _items(session.exec(select(OperationalRun).where(OperationalRun.project_id == project_id)))

    return ProjectTabStats(
        requirements=len(requirements),
        blocks=len(blocks),
        tests=len(tests),
        baselines=len(baselines),
        change_requests=len(change_requests),
        non_conformities=len(non_conformities),
        simulation_evidence=len(simulation_evidence),
        operational_evidence=len(operational_evidence),
        operational_runs=len(operational_runs),
    )

def export_project_bundle(session: Session, project_id: UUID) -> dict[str, Any]:
    from app.services.registry_service import build_step_ap242_contract, build_sysml_mapping_contract

    project = get_project_service(session, project_id)
    connectors = list_connectors(session, project_id)
    external_artifacts = list_external_artifacts(session, project_id)
    fmi_contracts = list_fmi_contracts(session, project_id)
    external_artifact_versions = [
        ExternalArtifactVersionRead.model_validate(item)
        for item in _items(
            session.exec(
                select(ExternalArtifactVersion)
                .join(ExternalArtifact)
                .where(ExternalArtifact.project_id == project_id)
                .order_by(desc(ExternalArtifactVersion.created_at))
            )
        )
    ]
    artifact_links = list_artifact_links(session, project_id)
    verification_evidence = list_verification_evidence(session, project_id)
    simulation_evidence = list_simulation_evidence(session, project_id)
    operational_evidence = list_operational_evidence(session, project_id)
    sysml_mapping_contract = build_sysml_mapping_contract(session, project_id)
    step_ap242_contract = build_step_ap242_contract(session, project_id)
    operational_evidence_links = [
        OperationalEvidenceLinkRead.model_validate(item).model_dump(mode="json")
        for item in _items(
            session.exec(
                select(OperationalEvidenceLink)
                .join(OperationalEvidence)
                .where(OperationalEvidence.project_id == project_id)
                .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
            )
        )
    ]
    simulation_evidence_links = [
        SimulationEvidenceLinkRead.model_validate(item).model_dump(mode="json")
        for item in _items(
            session.exec(
                select(SimulationEvidenceLink)
                .join(SimulationEvidence)
                .where(SimulationEvidence.project_id == project_id)
                .order_by(SimulationEvidenceLink.created_at, SimulationEvidenceLink.id)
            )
        )
    ]
    configuration_contexts = list_configuration_contexts(session, project_id)
    configuration_item_mappings = [
        ConfigurationItemMappingRead.model_validate(item)
        for item in _items(
            session.exec(
                select(ConfigurationItemMapping)
                .join(ConfigurationContext)
                .where(ConfigurationContext.project_id == project_id)
                .order_by(ConfigurationItemMapping.created_at)
            )
        )
    ]
    bundle = {
        "schema": "threadlite.project.export.v1",
        "exported_at": utcnow().isoformat(),
        "project": project.model_dump(mode="json"),
        "dashboard": get_project_dashboard(session, project_id).model_dump(mode="json"),
        "requirements": [RequirementRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))],
        "blocks": [BlockRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Block).where(Block.project_id == project_id)))],
        "block_containments": [BlockContainmentRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(BlockContainment).where(BlockContainment.project_id == project_id)))],
        "components": [ComponentRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Component).where(Component.project_id == project_id)))],
        "test_cases": [TestCaseRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(TestCase).where(TestCase.project_id == project_id)))],
        "test_runs": [TestRunRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(TestRun).join(TestCase).where(TestCase.project_id == project_id)))],
        "operational_runs": [OperationalRunRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(OperationalRun).where(OperationalRun.project_id == project_id)))],
        "links": [LinkRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Link).where(Link.project_id == project_id)))],
        "sysml_relations": [SysMLRelationRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id)))],
        "baselines": [
            {
                "baseline": BaselineRead.model_validate(baseline).model_dump(mode="json"),
                "items": [BaselineItemRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline.id)))],
            }
            for baseline in _items(session.exec(select(Baseline).where(Baseline.project_id == project_id)))
        ],
        "non_conformities": [NonConformityRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id)))],
        "verification_evidence": [evidence.model_dump(mode="json") for evidence in verification_evidence],
        "simulation_evidence": [evidence.model_dump(mode="json") for evidence in simulation_evidence],
        "simulation_evidence_links": simulation_evidence_links,
        "fmi_contracts": [contract.model_dump(mode="json") for contract in fmi_contracts],
        "operational_evidence": [evidence.model_dump(mode="json") for evidence in operational_evidence],
        "operational_evidence_links": operational_evidence_links,
        "sysml_mapping_contract": sysml_mapping_contract.model_dump(mode="json"),
        "step_ap242_contract": step_ap242_contract.model_dump(mode="json"),
        "change_requests": [ChangeRequestRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "change_impacts": [ChangeImpactRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeImpact).join(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "approval_action_logs": [ApprovalActionLogRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ApprovalActionLog).where(ApprovalActionLog.project_id == project_id)))],
        "revision_snapshots": [RevisionSnapshotRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project_id)))],
        "connectors": [connector.model_dump(mode="json") for connector in connectors],
        "external_artifacts": [artifact.model_dump(mode="json") for artifact in external_artifacts],
        "external_artifact_versions": [version.model_dump(mode="json") for version in external_artifact_versions],
        "artifact_links": [link.model_dump(mode="json") for link in artifact_links],
        "configuration_contexts": [context.model_dump(mode="json") for context in configuration_contexts],
        "configuration_item_mappings": [mapping.model_dump(mode="json") for mapping in configuration_item_mappings],
        "authoritative_registry_summary": get_authoritative_registry_summary(session, project_id).model_dump(mode="json"),
    }
    return bundle

def list_review_queue(session: Session, project_id: UUID) -> ReviewQueueResponse:
    project = get_project_service(session, project_id)
    items: list[ReviewQueueItem] = []
    for model, object_type, status_value in (
        (Requirement, "requirement", RequirementStatus.in_review),
        (Block, "block", BlockStatus.in_review),
        (TestCase, "test_case", TestCaseStatus.in_review),
    ):
        rows = _items(session.exec(select(model).where(model.project_id == project_id, model.status == status_value)))
        for row in rows:
            items.append(
                ReviewQueueItem(
                    object_type=object_type,
                    id=row.id,
                    key=row.key,
                    title=getattr(row, "title", getattr(row, "name", "")),
                    status=_status_value(row.status),
                    version=row.version,
                    updated_at=row.updated_at,
                )
            )
    return ReviewQueueResponse(project=project, items=sorted(items, key=lambda item: item.updated_at, reverse=True))

__all__ = [
    "list_projects_service",
    "get_project_service",
    "create_project",
    "update_project",
    "get_project_dashboard",
    "get_project_tab_stats",
    "export_project_bundle",
    "list_review_queue",
]
