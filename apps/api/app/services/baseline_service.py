"""Baseline Service service layer for the DigitalThread API."""

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
from app.services.configuration_service import list_configuration_contexts, list_configuration_item_mappings

def create_baseline(session: Session, payload: BaselineCreate) -> tuple[BaselineRead, list[BaselineItemRead]]:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    baseline = _add(session, Baseline.model_validate(payload))
    _log_action(
        session,
        object_type="baseline",
        obj=baseline,
        from_status=_status_value(baseline.status),
        to_status=_status_value(baseline.status),
        action="create",
        actor=None,
        comment=baseline.description,
    )
    items: list[BaselineItemRead] = []
    for object_type, model, selected_ids in (
        (BaselineObjectType.requirement, Requirement, set(payload.requirement_ids) or None),
        (BaselineObjectType.block, Block, set(payload.block_ids) or None),
        (BaselineObjectType.component, Component, None),
        (BaselineObjectType.test_case, TestCase, set(payload.test_case_ids) or None),
    ):
        for row in _items(session.exec(select(model).where(model.project_id == payload.project_id))):
            obj = row[0] if not hasattr(row, "id") else row
            if object_type != BaselineObjectType.component and getattr(obj, "status", None) is not None and _status_value(obj.status) != "approved":
                continue
            if selected_ids and obj.id not in selected_ids:
                continue
            bi = _add(session, BaselineItem(baseline_id=baseline.id, object_type=object_type, object_id=obj.id, object_version=getattr(obj, "version", 1)))
            items.append(BaselineItemRead.model_validate(bi))
    return BaselineRead.model_validate(baseline), items

def release_baseline(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BaselineRead:
    baseline = _get(session, Baseline, obj_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    if baseline.status == BaselineStatus.released:
        return _read(BaselineRead, baseline)
    if baseline.status != BaselineStatus.draft:
        raise ValueError("Only draft baselines can be released.")
    old = _status_value(baseline.status)
    baseline.status = BaselineStatus.released
    _touch(baseline)
    _commit(session, baseline)
    _log_action(
        session,
        object_type="baseline",
        obj=baseline,
        from_status=old,
        to_status="released",
        action="release",
        actor=payload.actor if payload else None,
        comment=payload.comment if payload else None,
    )
    return _read(BaselineRead, baseline)

def obsolete_baseline(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BaselineRead:
    baseline = _get(session, Baseline, obj_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    if baseline.status == BaselineStatus.obsolete:
        return _read(BaselineRead, baseline)
    if baseline.status not in {BaselineStatus.draft, BaselineStatus.released}:
        raise ValueError("Only draft or released baselines can be marked obsolete.")
    old = _status_value(baseline.status)
    baseline.status = BaselineStatus.obsolete
    _touch(baseline)
    _commit(session, baseline)
    _log_action(
        session,
        object_type="baseline",
        obj=baseline,
        from_status=old,
        to_status="obsolete",
        action="obsolete",
        actor=payload.actor if payload else None,
        comment=payload.comment if payload else None,
    )
    return _read(BaselineRead, baseline)

def list_baselines(session: Session, project_id: UUID) -> list[BaselineRead]:
    return [BaselineRead.model_validate(item) for item in _items(session.exec(select(Baseline).where(Baseline.project_id == project_id).order_by(desc(Baseline.created_at))))]

def get_baseline_detail(session: Session, baseline_id: UUID) -> dict[str, Any]:
    baseline = _get(session, Baseline, baseline_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    items = [BaselineItemRead.model_validate(item) for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline_id)))]
    related_contexts: list[ConfigurationContextRead] = []
    baseline_signature = {(item.object_type.value, item.object_id, item.object_version) for item in items}
    if baseline_signature:
        for context in list_configuration_contexts(session, baseline.project_id):
            context_signatures = {
                (item.internal_object_type.value, item.internal_object_id, item.internal_object_version)
                for item in list_configuration_item_mappings(session, context.id)
                if item.internal_object_id is not None and item.internal_object_type is not None and item.internal_object_version is not None
            }
            if baseline_signature.issubset(context_signatures):
                related_contexts.append(context)
    bridge_context = BaselineBridgeContextRead(
        id=baseline.id,
        project_id=baseline.project_id,
        key=f"BASELINE-{str(baseline.id)[:8].upper()}",
        name=f"{baseline.name} bridge",
        description=baseline.description or "Read-only configuration-context projection for this baseline.",
        context_type=ConfigurationContextType.review_gate,
        status=ConfigurationContextStatus.frozen,
        created_at=baseline.created_at,
        updated_at=baseline.updated_at,
        item_count=len(items),
        baseline_id=baseline.id,
        baseline_name=baseline.name,
    )
    return {
        "baseline": BaselineRead.model_validate(baseline),
        "bridge_context": bridge_context,
        "items": items,
        "related_configuration_contexts": related_contexts,
        "history": list_baseline_history(session, baseline_id),
    }

def list_baseline_history(session: Session, baseline_id: UUID) -> list[ApprovalActionLogRead]:
    rows = _items(
        session.exec(
            select(ApprovalActionLog)
            .where(ApprovalActionLog.object_type == "baseline", ApprovalActionLog.object_id == baseline_id)
            .order_by(desc(ApprovalActionLog.created_at), desc(ApprovalActionLog.id))
        )
    )
    return [ApprovalActionLogRead.model_validate(item) for item in rows]

def get_baseline_bridge_context(session: Session, baseline_id: UUID) -> BaselineBridgeContextRead:
    detail = get_baseline_detail(session, baseline_id)
    return detail["bridge_context"]

def compare_baselines(session: Session, left_baseline_id: UUID, right_baseline_id: UUID) -> BaselineComparisonResponse:
    left_baseline = _get(session, Baseline, left_baseline_id)
    if left_baseline is None:
        raise LookupError("Baseline not found")
    right_baseline = _get(session, Baseline, right_baseline_id)
    if right_baseline is None:
        raise LookupError("Baseline not found")
    if left_baseline.project_id != right_baseline.project_id:
        raise ValueError("Baselines must belong to the same project")

    left_entries = [
        _baseline_comparison_entry(session, left_baseline.project_id, item)
        for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == left_baseline_id)))
    ]
    right_entries = [
        _baseline_comparison_entry(session, right_baseline.project_id, item)
        for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == right_baseline_id)))
    ]
    groups, summary = _compare_configuration_entry_groups(left_entries, right_entries)

    return BaselineComparisonResponse(
        left_baseline=_read(BaselineRead, left_baseline),
        right_baseline=_read(BaselineRead, right_baseline),
        summary=summary,
        groups=groups,
    )

__all__ = [
    "create_baseline",
    "release_baseline",
    "obsolete_baseline",
    "list_baselines",
    "get_baseline_detail",
    "list_baseline_history",
    "get_baseline_bridge_context",
    "compare_baselines",
]
