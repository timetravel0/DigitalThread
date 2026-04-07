"""Test Service service layer for the DigitalThread API."""

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

def create_test_case(session: Session, payload: TestCaseCreate) -> TestCaseRead:
    item = TestCase.model_validate(payload)
    if item.status == TestCaseStatus.approved and item.approved_at is None:
        item.approved_at = datetime.now(timezone.utc)
        item.approved_by = "seed"
    _commit(session, item)
    _snapshot(session, "test_case", item, "Created test case")
    return _read(TestCaseRead, item)

def update_test_case(session: Session, obj_id: UUID, payload: TestCaseUpdate) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if not _editable(item.status):
        raise ValueError("Approved and obsolete test cases cannot be edited in place.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    _commit(session, item)
    _snapshot(session, "test_case", item, "Updated test case")
    return _read(TestCaseRead, item)

def create_test_case_draft_version(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if item.status != TestCaseStatus.approved:
        raise ValueError("Draft versions can only be created from approved test cases.")
    released_baselines = _released_baselines_for_object(session, item.project_id, BaselineObjectType.test_case, item.id)
    if released_baselines:
        _ensure_change_request_for_released_baseline(
            session,
            project_id=item.project_id,
            object_type="test_case",
            object_id=item.id,
            object_label=f"{item.key} - {item.title}",
            reason=f"Released baseline(s) {', '.join(b.name for b in released_baselines)} include this test case and a draft version has been created.",
        )
    draft = TestCase(
        project_id=item.project_id,
        key=item.key,
        title=item.title,
        description=item.description,
        method=item.method,
        status=TestCaseStatus.draft,
        version=item.version + 1,
        review_comment=payload.change_summary if payload else None,
    )
    _commit(session, draft)
    _snapshot(session, "test_case", draft, "Created draft version", payload.actor if payload else None)
    return _read(TestCaseRead, draft)

def submit_test_case_for_review(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if not _editable(item.status):
        raise ValueError("Only draft or rejected test cases can be submitted for review.")
    old = _status_value(item.status)
    item.status = TestCaseStatus.in_review
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="test_case", obj=item, from_status=old, to_status="in_review", action="submit_review", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "test_case", item, "Submitted for review", payload.actor if payload else None)
    return _read(TestCaseRead, item)

def approve_test_case(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if item.status != TestCaseStatus.in_review:
        raise ValueError("Only test cases in review can be approved.")
    old = _status_value(item.status)
    item.status = TestCaseStatus.approved
    item.approved_at = datetime.now(timezone.utc)
    item.approved_by = payload.actor if payload and payload.actor else "system"
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="test_case", obj=item, from_status=old, to_status="approved", action="approve", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "test_case", item, "Approved test case", payload.actor if payload else None)
    return _read(TestCaseRead, item)

def reject_test_case(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if item.status != TestCaseStatus.in_review:
        raise ValueError("Only test cases in review can be rejected.")
    old = _status_value(item.status)
    item.status = TestCaseStatus.rejected
    item.rejection_reason = payload.reason if payload and payload.reason else payload.comment if payload else None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="test_case", obj=item, from_status=old, to_status="rejected", action="reject", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "test_case", item, "Rejected test case", payload.actor if payload else None)
    return _read(TestCaseRead, item)

def send_test_case_back_to_draft(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    if item.status not in {TestCaseStatus.in_review, TestCaseStatus.rejected}:
        raise ValueError("Only test cases in review or rejected test cases can be sent back to draft.")
    old = _status_value(item.status)
    item.status = TestCaseStatus.draft
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="test_case", obj=item, from_status=old, to_status="draft", action="send_back_to_draft", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "test_case", item, "Sent back to draft", payload.actor if payload else None)
    return _read(TestCaseRead, item)

def list_test_case_history(session: Session, obj_id: UUID) -> list[RevisionSnapshotRead]:
    rows = _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.object_type == "test_case", RevisionSnapshot.object_id == obj_id).order_by(desc(RevisionSnapshot.changed_at))))
    return [RevisionSnapshotRead.model_validate(item) for item in rows]

def list_test_cases(session: Session, project_id: UUID) -> list[TestCaseRead]:
    return [TestCaseRead.model_validate(item) for item in _items(session.exec(select(TestCase).where(TestCase.project_id == project_id).order_by(TestCase.key)))]

def create_test_run(session: Session, payload: TestRunCreate) -> TestRunRead:
    if _get(session, TestCase, payload.test_case_id) is None:
        raise LookupError("Test case not found")
    return _read(TestRunRead, _add(session, TestRun.model_validate(payload)))

def list_test_runs(session: Session, project_id: UUID) -> list[TestRunRead]:
    stmt = select(TestRun).join(TestCase, TestRun.test_case_id == TestCase.id).where(TestCase.project_id == project_id).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))
    return [TestRunRead.model_validate(item) for item in _items(session.exec(stmt))]

__all__ = [
    "create_test_case",
    "update_test_case",
    "create_test_case_draft_version",
    "submit_test_case_for_review",
    "approve_test_case",
    "reject_test_case",
    "send_test_case_back_to_draft",
    "list_test_case_history",
    "list_test_cases",
    "create_test_run",
    "list_test_runs",
]
