"""Non Conformity Service service layer for the DigitalThread API."""

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
from app.services.evidence_service import list_verification_evidence

def create_non_conformity(session: Session, payload: NonConformityCreate) -> NonConformityRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    item = _add(session, NonConformity.model_validate(payload))
    _log_action(
        session,
        object_type="non_conformity",
        obj=item,
        from_status=_status_value(item.status),
        to_status=_status_value(item.status),
        action="create",
        actor=None,
        comment=payload.review_comment or payload.description,
    )
    _snapshot(session, "non_conformity", item, "Created non-conformity", None)
    return _read(NonConformityRead, item)

def update_non_conformity(session: Session, obj_id: UUID, payload: NonConformityUpdate) -> NonConformityRead:
    item = _get(session, NonConformity, obj_id)
    if item is None:
        raise LookupError("Non-conformity not found")
    before_status = _status_value(item.status)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    _commit(session, item)
    if before_status != _status_value(item.status) or payload.disposition is not None:
        _log_action(
            session,
            object_type="non_conformity",
            obj=item,
            from_status=before_status,
            to_status=_status_value(item.status),
            action="update",
            actor=None,
            comment=payload.description,
        )
    _snapshot(session, "non_conformity", item, "Updated non-conformity", None)
    return _read(NonConformityRead, item)

def list_non_conformities(session: Session, project_id: UUID) -> list[NonConformityRead]:
    return [NonConformityRead.model_validate(item) for item in _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id).order_by(desc(NonConformity.created_at))))]

def get_non_conformity_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, NonConformity, obj_id)
    if item is None:
        raise LookupError("Non-conformity not found")
    impacts = list_links(session, item.project_id, "non_conformity", item.id)
    impact_summary: list[ObjectSummary] = []
    for link in impacts:
        if link.source_type == LinkObjectType.non_conformity and link.target_type.value in OBJECT_MODELS:
            impact_summary.append(summarize(resolve_object(session, link.target_type.value, link.target_id)))
        elif link.target_type == LinkObjectType.non_conformity and link.source_type.value in OBJECT_MODELS:
            impact_summary.append(summarize(resolve_object(session, link.source_type.value, link.source_id)))
    related_requirements = [
        summarize(resolve_object(session, link.target_type.value, link.target_id))
        for link in impacts
        if link.source_type == LinkObjectType.non_conformity and link.target_type == LinkObjectType.requirement
    ]
    return {
        "non_conformity": NonConformityRead.model_validate(item),
        "links": impacts,
        "related_requirements": related_requirements,
        "verification_evidence": list_verification_evidence(session, item.project_id, internal_object_type=FederatedInternalObjectType.non_conformity, internal_object_id=item.id),
        "history": [ApprovalActionLogRead.model_validate(row) for row in _items(session.exec(select(ApprovalActionLog).where(ApprovalActionLog.project_id == item.project_id, ApprovalActionLog.object_type == "non_conformity", ApprovalActionLog.object_id == item.id).order_by(desc(ApprovalActionLog.created_at))))],
        "impact": build_impact(session, item.project_id, "non_conformity", item.id),
        "impact_summary": impact_summary,
    }

__all__ = [
    "create_non_conformity",
    "update_non_conformity",
    "list_non_conformities",
    "get_non_conformity_detail",
]
