"""Evidence Service service layer for the DigitalThread API."""

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
from app.impact_service import build_impact
from app.services.link_service import list_links

def create_verification_evidence(session: Session, payload: VerificationEvidenceCreate) -> VerificationEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_test_case_ids = list(dict.fromkeys(payload.linked_test_case_ids))
    linked_component_ids = list(dict.fromkeys(payload.linked_component_ids))
    linked_non_conformity_ids = list(dict.fromkeys(payload.linked_non_conformity_ids))
    if not linked_requirement_ids and not linked_test_case_ids and not linked_component_ids and not linked_non_conformity_ids:
        raise ValueError("Verification evidence must link to at least one requirement, test case, component, or non-conformity")
    for requirement_id in linked_requirement_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.requirement, requirement_id)
    for test_case_id in linked_test_case_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.test_case, test_case_id)
    for component_id in linked_component_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.component, component_id)
    for non_conformity_id in linked_non_conformity_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.non_conformity, non_conformity_id)
    evidence = VerificationEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_test_case_ids", "linked_component_ids", "linked_non_conformity_ids"}))
    link_rows: list[VerificationEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for test_case_id in linked_test_case_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=test_case_id,
            )
        )
    for component_id in linked_component_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.component,
                internal_object_id=component_id,
            )
        )
    for non_conformity_id in linked_non_conformity_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.non_conformity,
                internal_object_id=non_conformity_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _verification_evidence_read(session, evidence, link_rows)

def list_verification_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: FederatedInternalObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[VerificationEvidenceRead]:
    evidence_rows = _items(session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project_id).order_by(desc(VerificationEvidence.created_at))))
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(VerificationEvidenceLink)
            .where(VerificationEvidenceLink.verification_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(VerificationEvidenceLink.created_at, VerificationEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[VerificationEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.verification_evidence_id].append(link)
    reads: list[VerificationEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_verification_evidence_read(session, evidence, evidence_links))
    return reads

def get_verification_evidence_service(session: Session, evidence_id: UUID) -> VerificationEvidenceRead:
    evidence = _get(session, VerificationEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Verification evidence not found")
    return _verification_evidence_read(session, evidence)

def create_simulation_evidence(session: Session, payload: SimulationEvidenceCreate) -> SimulationEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_test_case_ids = list(dict.fromkeys(payload.linked_test_case_ids))
    linked_verification_evidence_ids = list(dict.fromkeys(payload.linked_verification_evidence_ids))
    if payload.fmi_contract_id is not None:
        _validate_fmi_contract(session, payload.fmi_contract_id, payload.project_id)
    if not linked_requirement_ids and not linked_test_case_ids and not linked_verification_evidence_ids:
        raise ValueError("Simulation evidence must link to at least one requirement, test case, or verification evidence")
    for requirement_id in linked_requirement_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.requirement, requirement_id)
    for test_case_id in linked_test_case_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.test_case, test_case_id)
    for verification_evidence_id in linked_verification_evidence_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.verification_evidence, verification_evidence_id)
    evidence = SimulationEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_test_case_ids", "linked_verification_evidence_ids"}))
    link_rows: list[SimulationEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for test_case_id in linked_test_case_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.test_case,
                internal_object_id=test_case_id,
            )
        )
    for verification_evidence_id in linked_verification_evidence_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.verification_evidence,
                internal_object_id=verification_evidence_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _simulation_evidence_read(session, evidence, link_rows)

def list_simulation_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: SimulationEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[SimulationEvidenceRead]:
    evidence_rows = _items(
        session.exec(
            select(SimulationEvidence)
            .where(SimulationEvidence.project_id == project_id)
            .order_by(desc(SimulationEvidence.execution_timestamp), desc(SimulationEvidence.created_at))
        )
    )
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(SimulationEvidenceLink)
            .where(SimulationEvidenceLink.simulation_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(SimulationEvidenceLink.created_at, SimulationEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[SimulationEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.simulation_evidence_id].append(link)
    reads: list[SimulationEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_simulation_evidence_read(session, evidence, evidence_links))
    return reads

def get_simulation_evidence_service(session: Session, evidence_id: UUID) -> SimulationEvidenceRead:
    evidence = _get(session, SimulationEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Simulation evidence not found")
    return _simulation_evidence_read(session, evidence)

def create_operational_evidence(session: Session, payload: OperationalEvidenceCreate) -> OperationalEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_verification_evidence_ids = list(dict.fromkeys(payload.linked_verification_evidence_ids))
    if not linked_requirement_ids and not linked_verification_evidence_ids:
        raise ValueError("Operational evidence must link to at least one requirement or verification evidence")
    if payload.coverage_window_end < payload.coverage_window_start:
        raise ValueError("Operational evidence coverage window end must be after the start")
    for requirement_id in linked_requirement_ids:
        _validate_operational_evidence_link(session, payload.project_id, OperationalEvidenceLinkObjectType.requirement, requirement_id)
    for verification_evidence_id in linked_verification_evidence_ids:
        _validate_operational_evidence_link(session, payload.project_id, OperationalEvidenceLinkObjectType.verification_evidence, verification_evidence_id)
    evidence = OperationalEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_verification_evidence_ids"}))
    link_rows: list[OperationalEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            OperationalEvidenceLink(
                operational_evidence_id=evidence.id,
                internal_object_type=OperationalEvidenceLinkObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for verification_evidence_id in linked_verification_evidence_ids:
        link_rows.append(
            OperationalEvidenceLink(
                operational_evidence_id=evidence.id,
                internal_object_type=OperationalEvidenceLinkObjectType.verification_evidence,
                internal_object_id=verification_evidence_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _operational_evidence_read(session, evidence, link_rows)

def list_operational_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: OperationalEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[OperationalEvidenceRead]:
    evidence_rows = _items(
        session.exec(
            select(OperationalEvidence)
            .where(OperationalEvidence.project_id == project_id)
            .order_by(desc(OperationalEvidence.captured_at), desc(OperationalEvidence.created_at))
        )
    )
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(OperationalEvidenceLink)
            .where(OperationalEvidenceLink.operational_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[OperationalEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.operational_evidence_id].append(link)
    reads: list[OperationalEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_operational_evidence_read(session, evidence, evidence_links))
    return reads

def get_operational_evidence_service(session: Session, evidence_id: UUID) -> OperationalEvidenceRead:
    evidence = _get(session, OperationalEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Operational evidence not found")
    return _operational_evidence_read(session, evidence)

def create_operational_run(session: Session, payload: OperationalRunCreate) -> OperationalRunRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    return _read(OperationalRunRead, _add(session, OperationalRun.model_validate(payload)))

def update_operational_run(session: Session, obj_id: UUID, payload: OperationalRunUpdate) -> OperationalRunRead:
    item = _get(session, OperationalRun, obj_id)
    if item is None:
        raise LookupError("Operational run not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(OperationalRunRead, _add(session, item))

def list_operational_runs(session: Session, project_id: UUID) -> list[OperationalRunRead]:
    return [OperationalRunRead.model_validate(item) for item in _items(session.exec(select(OperationalRun).where(OperationalRun.project_id == project_id).order_by(desc(OperationalRun.date))))]

def get_operational_run_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, OperationalRun, obj_id)
    if item is None:
        raise LookupError("Operational run not found")
    return {
        "operational_run": OperationalRunRead.model_validate(item),
        "links": list_links(session, item.project_id, "operational_run", item.id),
        "impact": build_impact(session, item.project_id, "operational_run", item.id),
    }

__all__ = [
    "create_verification_evidence",
    "list_verification_evidence",
    "get_verification_evidence_service",
    "create_simulation_evidence",
    "list_simulation_evidence",
    "get_simulation_evidence_service",
    "create_operational_evidence",
    "list_operational_evidence",
    "get_operational_evidence_service",
    "create_operational_run",
    "update_operational_run",
    "list_operational_runs",
    "get_operational_run_detail",
]
