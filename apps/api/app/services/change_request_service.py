"""Change Request Service service layer for the DigitalThread API."""

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
from app.services.link_service import list_links

def create_change_request(session: Session, payload: ChangeRequestCreate) -> ChangeRequestRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    item = ChangeRequest.model_validate(payload)
    if item.status != ChangeRequestStatus.open:
        raise ValueError("Change requests must be created in the open state.")
    return _read(ChangeRequestRead, _add(session, item))

def update_change_request(session: Session, obj_id: UUID, payload: ChangeRequestUpdate) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status in {ChangeRequestStatus.implemented, ChangeRequestStatus.closed}:
        raise ValueError("Implemented and closed change requests cannot be edited in place.")
    if payload.status is not None and payload.status != item.status:
        raise ValueError("Change request status must be updated through workflow actions.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "status":
            continue
        setattr(item, k, v)
    _touch(item)
    return _read(ChangeRequestRead, _add(session, item))

def list_change_requests(session: Session, project_id: UUID) -> list[ChangeRequestRead]:
    return [ChangeRequestRead.model_validate(item) for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id).order_by(desc(ChangeRequest.created_at))))]

def list_change_request_history(session: Session, obj_id: UUID) -> list[ApprovalActionLogRead]:
    return _decision_history(session, "change_request", obj_id, newest_first=False)

def submit_change_request_for_analysis(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status not in {ChangeRequestStatus.open, ChangeRequestStatus.rejected}:
        raise ValueError("Only open or rejected change requests can move to analysis.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.analysis
    item.analysis_summary = payload.comment or payload.reason or item.analysis_summary
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="analysis", action="submit_analysis", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def approve_change_request(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status != ChangeRequestStatus.analysis:
        raise ValueError("Only change requests in analysis can be approved.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.approved
    item.disposition_summary = payload.comment or payload.reason or item.disposition_summary
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="approved", action="approve", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def reject_change_request(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status != ChangeRequestStatus.analysis:
        raise ValueError("Only change requests in analysis can be rejected.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.rejected
    item.disposition_summary = payload.comment or payload.reason or item.disposition_summary
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="rejected", action="reject", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def reopen_change_request(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status not in {ChangeRequestStatus.rejected, ChangeRequestStatus.closed}:
        raise ValueError("Only rejected or closed change requests can be reopened.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.open
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="open", action="reopen", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def mark_change_request_implemented(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status != ChangeRequestStatus.approved:
        raise ValueError("Only approved change requests can be marked implemented.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.implemented
    item.implementation_summary = payload.comment or payload.reason or item.implementation_summary
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="implemented", action="implement", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def close_change_request(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status != ChangeRequestStatus.implemented:
        raise ValueError("Only implemented change requests can be closed.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.closed
    item.closure_summary = payload.comment or payload.reason or item.closure_summary
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="change_request", obj=item, from_status=old, to_status="closed", action="close", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    return _read(ChangeRequestRead, item)

def create_change_impact(session: Session, payload: ChangeImpactCreate) -> ChangeImpactRead:
    if _get(session, ChangeRequest, payload.change_request_id) is None:
        raise LookupError("Change request not found")
    return _read(ChangeImpactRead, _add(session, ChangeImpact.model_validate(payload)))

def list_change_impacts(session: Session, change_request_id: UUID) -> list[ChangeImpactRead]:
    return [ChangeImpactRead.model_validate(item) for item in _items(session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == change_request_id)))]

def get_change_request_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    impacts = list_change_impacts(session, obj_id)
    return {
        "change_request": ChangeRequestRead.model_validate(item),
        "impacts": impacts,
        "impact_summary": [summarize(resolve_object(session, x.object_type, x.object_id)) for x in impacts if x.object_type in OBJECT_MODELS],
        "history": list_change_request_history(session, item.id),
    }

__all__ = [
    "create_change_request",
    "update_change_request",
    "list_change_requests",
    "list_change_request_history",
    "submit_change_request_for_analysis",
    "approve_change_request",
    "reject_change_request",
    "reopen_change_request",
    "mark_change_request_implemented",
    "close_change_request",
    "create_change_impact",
    "list_change_impacts",
    "get_change_request_detail",
]
