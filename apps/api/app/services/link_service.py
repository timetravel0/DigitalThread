"""Link Service service layer for the DigitalThread API."""

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

def create_link(session: Session, payload: LinkCreate) -> LinkRead:
    source = resolve_object(session, payload.source_type.value, payload.source_id)
    target = resolve_object(session, payload.target_type.value, payload.target_id)
    if source["project_id"] != target["project_id"] or source["project_id"] != payload.project_id:
        raise ValueError("Links must stay within the same project")
    if payload.source_type == LinkObjectType.test_run and payload.target_type not in {LinkObjectType.requirement, LinkObjectType.component, LinkObjectType.test_case}:
        raise ValueError("TestRun can only link to requirement, component, or test_case")
    if payload.target_type == LinkObjectType.test_run and payload.source_type not in {LinkObjectType.requirement, LinkObjectType.component, LinkObjectType.test_case}:
        raise ValueError("TestRun can only be linked from requirement, component, or test_case")
    return _read(LinkRead, _add(session, Link.model_validate(payload)))

def delete_link(session: Session, link_id: UUID) -> None:
    item = _get(session, Link, link_id)
    if item is None:
        raise LookupError("Link not found")
    session.delete(item)
    session.commit()

def list_links(session: Session, project_id: UUID, object_type: str | None = None, object_id: UUID | None = None) -> list[LinkRead]:
    stmt = select(Link).where(Link.project_id == project_id)
    if object_type and object_id:
        otype = LinkObjectType(object_type)
        stmt = stmt.where(((Link.source_type == otype) & (Link.source_id == object_id)) | ((Link.target_type == otype) & (Link.target_id == object_id)))
    links = [LinkRead.model_validate(item) for item in _items(session.exec(stmt.order_by(Link.created_at)))]
    for link in links:
        try:
            src = resolve_object(session, link.source_type.value, link.source_id)
            link.source_label = src["label"]
        except LookupError:
            link.source_label = f"{link.source_type.value}:{link.source_id}"
        try:
            tgt = resolve_object(session, link.target_type.value, link.target_id)
            link.target_label = tgt["label"]
        except LookupError:
            link.target_label = f"{link.target_type.value}:{link.target_id}"
    return links

def create_sysml_relation(session: Session, payload: SysMLRelationCreate) -> SysMLRelationRead:
    source = resolve_object(session, payload.source_type.value, payload.source_id)
    target = resolve_object(session, payload.target_type.value, payload.target_id)
    if source["project_id"] != target["project_id"] or source["project_id"] != payload.project_id:
        raise ValueError("SysML relations must stay within the same project")
    _validate_sysml_relation_pattern(payload)
    return SysMLRelationRead.model_validate(_add(session, SysMLRelation.model_validate(payload)))

def delete_sysml_relation(session: Session, relation_id: UUID) -> None:
    item = _get(session, SysMLRelation, relation_id)
    if item is None:
        raise LookupError("SysML relation not found")
    session.delete(item)
    session.commit()

def list_sysml_relations(session: Session, project_id: UUID, object_type: str | None = None, object_id: UUID | None = None) -> list[SysMLRelationRead]:
    stmt = select(SysMLRelation).where(SysMLRelation.project_id == project_id)
    if object_type and object_id:
        stype = SysMLObjectType(object_type)
        stmt = stmt.where(or_(and_(SysMLRelation.source_type == stype, SysMLRelation.source_id == object_id), and_(SysMLRelation.target_type == stype, SysMLRelation.target_id == object_id)))
    return [SysMLRelationRead.model_validate(item) for item in _items(session.exec(stmt.order_by(SysMLRelation.created_at)))]

__all__ = [
    "create_link",
    "delete_link",
    "list_links",
    "create_sysml_relation",
    "delete_sysml_relation",
    "list_sysml_relations",
]
