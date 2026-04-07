"""Requirement Service service layer for the DigitalThread API."""

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

def create_requirement(session: Session, payload: RequirementCreate) -> RequirementRead:
    item = Requirement.model_validate(payload)
    if item.status == RequirementStatus.approved and item.approved_at is None:
        item.approved_at = datetime.now(timezone.utc)
        item.approved_by = "seed"
    _commit(session, item)
    _snapshot(session, "requirement", item, "Created requirement")
    return _read(RequirementRead, item)

def update_requirement(session: Session, obj_id: UUID, payload: RequirementUpdate) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if not _editable(item.status):
        raise ValueError("Approved and obsolete requirements cannot be edited in place.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    _commit(session, item)
    _snapshot(session, "requirement", item, "Updated requirement")
    return _read(RequirementRead, item)

def create_requirement_draft_version(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if item.status != RequirementStatus.approved:
        raise ValueError("Draft versions can only be created from approved requirements.")
    released_baselines = _released_baselines_for_object(session, item.project_id, BaselineObjectType.requirement, item.id)
    if released_baselines:
        _ensure_change_request_for_released_baseline(
            session,
            project_id=item.project_id,
            object_type="requirement",
            object_id=item.id,
            object_label=f"{item.key} - {item.title}",
            reason=f"Released baseline(s) {', '.join(b.name for b in released_baselines)} include this requirement and a draft version has been created.",
        )
    draft = Requirement(
        project_id=item.project_id,
        key=item.key,
        title=item.title,
        description=item.description,
        category=item.category,
        priority=item.priority,
        verification_method=item.verification_method,
        status=RequirementStatus.draft,
        version=item.version + 1,
        parent_requirement_id=item.parent_requirement_id,
        verification_criteria_json=dict(item.verification_criteria_json or {}),
        review_comment=payload.change_summary if payload else None,
    )
    _commit(session, draft)
    _snapshot(session, "requirement", draft, "Created draft version", payload.actor if payload else None)
    return _read(RequirementRead, draft)

def submit_requirement_for_review(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if not _editable(item.status):
        raise ValueError("Only draft or rejected requirements can be submitted for review.")
    old = _status_value(item.status)
    item.status = RequirementStatus.in_review
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="requirement", obj=item, from_status=old, to_status="in_review", action="submit_review", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "requirement", item, "Submitted for review", payload.actor if payload else None)
    return _read(RequirementRead, item)

def approve_requirement(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if item.status != RequirementStatus.in_review:
        raise ValueError("Only requirements in review can be approved.")
    old = _status_value(item.status)
    item.status = RequirementStatus.approved
    item.approved_at = datetime.now(timezone.utc)
    item.approved_by = payload.actor if payload and payload.actor else "system"
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="requirement", obj=item, from_status=old, to_status="approved", action="approve", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "requirement", item, "Approved requirement", payload.actor if payload else None)
    return _read(RequirementRead, item)

def reject_requirement(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if item.status != RequirementStatus.in_review:
        raise ValueError("Only requirements in review can be rejected.")
    old = _status_value(item.status)
    item.status = RequirementStatus.rejected
    item.rejection_reason = payload.reason if payload and payload.reason else payload.comment if payload else None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="requirement", obj=item, from_status=old, to_status="rejected", action="reject", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "requirement", item, "Rejected requirement", payload.actor if payload else None)
    return _read(RequirementRead, item)

def send_requirement_back_to_draft(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    if item.status not in {RequirementStatus.in_review, RequirementStatus.rejected}:
        raise ValueError("Only requirements in review or rejected requirements can be sent back to draft.")
    old = _status_value(item.status)
    item.status = RequirementStatus.draft
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="requirement", obj=item, from_status=old, to_status="draft", action="send_back_to_draft", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "requirement", item, "Sent back to draft", payload.actor if payload else None)
    return _read(RequirementRead, item)

def list_requirement_history(session: Session, obj_id: UUID) -> list[RevisionSnapshotRead]:
    rows = _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.object_type == "requirement", RevisionSnapshot.object_id == obj_id).order_by(desc(RevisionSnapshot.changed_at))))
    return [RevisionSnapshotRead.model_validate(item) for item in rows]

def list_requirements(session: Session, project_id: UUID, status: RequirementStatus | None = None, category: RequirementCategory | None = None, priority: Priority | None = None) -> list[RequirementRead]:
    stmt = select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.key)
    if status:
        stmt = stmt.where(Requirement.status == status)
    if category:
        stmt = stmt.where(Requirement.category == category)
    if priority:
        stmt = stmt.where(Requirement.priority == priority)
    return [RequirementRead.model_validate(item) for item in _items(session.exec(stmt))]

__all__ = [
    "create_requirement",
    "update_requirement",
    "create_requirement_draft_version",
    "submit_requirement_for_review",
    "approve_requirement",
    "reject_requirement",
    "send_requirement_back_to_draft",
    "list_requirement_history",
    "list_requirements",
]
