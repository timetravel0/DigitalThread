"""Federation Service service layer for the DigitalThread API."""

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

def list_connectors(session: Session, project_id: UUID) -> list[ConnectorDefinitionRead]:
    rows = _items(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project_id).order_by(ConnectorDefinition.name)))
    return [_connector_read(session, row) for row in rows]

def create_connector(session: Session, payload: ConnectorDefinitionCreate) -> ConnectorDefinitionRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    return _connector_read(session, _add(session, ConnectorDefinition.model_validate(payload)))

def update_connector(session: Session, obj_id: UUID, payload: ConnectorDefinitionUpdate) -> ConnectorDefinitionRead:
    item = _get(session, ConnectorDefinition, obj_id)
    if item is None:
        raise LookupError("Connector not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _connector_read(session, _add(session, item))

def get_connector_service(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, ConnectorDefinition, obj_id)
    if item is None:
        raise LookupError("Connector not found")
    artifacts = list_external_artifacts(session, item.project_id, connector_definition_id=item.id)
    return {"connector": _connector_read(session, item), "artifacts": artifacts}

def list_external_artifact_versions(session: Session, artifact_id: UUID) -> list[ExternalArtifactVersionRead]:
    rows = _items(session.exec(select(ExternalArtifactVersion).where(ExternalArtifactVersion.external_artifact_id == artifact_id).order_by(desc(ExternalArtifactVersion.created_at))))
    return [ExternalArtifactVersionRead.model_validate(item) for item in rows]

def create_external_artifact_version(session: Session, artifact_id: UUID, payload: ExternalArtifactVersionCreate) -> ExternalArtifactVersionRead:
    if _get(session, ExternalArtifact, artifact_id) is None:
        raise LookupError("External artifact not found")
    item = ExternalArtifactVersion(external_artifact_id=artifact_id, **payload.model_dump())
    return _read(ExternalArtifactVersionRead, _add(session, item))

def list_external_artifacts(
    session: Session,
    project_id: UUID,
    connector_definition_id: UUID | None = None,
    connector_type: ConnectorType | None = None,
    artifact_type: ExternalArtifactType | None = None,
) -> list[ExternalArtifactRead]:
    stmt = select(ExternalArtifact).where(ExternalArtifact.project_id == project_id)
    if connector_definition_id:
        stmt = stmt.where(ExternalArtifact.connector_definition_id == connector_definition_id)
    if artifact_type:
        stmt = stmt.where(ExternalArtifact.artifact_type == artifact_type)
    if connector_type is not None:
        connector_ids = [connector.id for connector in _items(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project_id, ConnectorDefinition.connector_type == connector_type)))]
        if not connector_ids:
            return []
        stmt = stmt.where(ExternalArtifact.connector_definition_id.in_(connector_ids))
    rows = _items(session.exec(stmt.order_by(ExternalArtifact.name)))
    return [_artifact_read(session, row) for row in rows]

def create_external_artifact(session: Session, payload: ExternalArtifactCreate) -> ExternalArtifactRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    if payload.connector_definition_id is not None:
        connector = _get(session, ConnectorDefinition, payload.connector_definition_id)
        if connector is None:
            raise LookupError("Connector not found")
        if connector.project_id != payload.project_id:
            raise ValueError("Connector must stay within the same project")
    return _artifact_read(session, _add(session, ExternalArtifact.model_validate(payload)))

def update_external_artifact(session: Session, obj_id: UUID, payload: ExternalArtifactUpdate) -> ExternalArtifactRead:
    item = _get(session, ExternalArtifact, obj_id)
    if item is None:
        raise LookupError("External artifact not found")
    if payload.connector_definition_id is not None:
        connector = _get(session, ConnectorDefinition, payload.connector_definition_id)
        if connector is None:
            raise LookupError("Connector not found")
        if connector.project_id != item.project_id:
            raise ValueError("Connector must stay within the same project")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _artifact_read(session, _add(session, item))

def get_external_artifact_service(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, ExternalArtifact, obj_id)
    if item is None:
        raise LookupError("External artifact not found")
    links = list_artifact_links(session, item.project_id, external_artifact_id=item.id)
    return {
        "external_artifact": _artifact_read(session, item),
        "versions": list_external_artifact_versions(session, item.id),
        "artifact_links": links,
    }

def list_artifact_links(
    session: Session,
    project_id: UUID,
    internal_object_type: FederatedInternalObjectType | None = None,
    internal_object_id: UUID | None = None,
    external_artifact_id: UUID | None = None,
) -> list[ArtifactLinkRead]:
    stmt = select(ArtifactLink).where(ArtifactLink.project_id == project_id)
    if internal_object_type and internal_object_id:
        stmt = stmt.where(and_(ArtifactLink.internal_object_type == internal_object_type, ArtifactLink.internal_object_id == internal_object_id))
    if external_artifact_id:
        stmt = stmt.where(ArtifactLink.external_artifact_id == external_artifact_id)
    rows = [ArtifactLinkRead.model_validate(item) for item in _items(session.exec(stmt.order_by(desc(ArtifactLink.created_at))))]
    for link in rows:
        raw = _get(session, ArtifactLink, link.id)
        if raw is None:
            continue
        link.internal_object_label = _resolve_artifact_link_internal_label(session, raw)
        artifact_name, version_label, connector_name = _resolve_artifact_link_external_label(session, raw)
        link.external_artifact_name = artifact_name
        link.external_artifact_version_label = version_label
        link.connector_name = connector_name
    return rows

def create_artifact_link(session: Session, payload: ArtifactLinkCreate) -> ArtifactLinkRead:
    _validate_internal_object(session, payload.internal_object_type, payload.internal_object_id, payload.project_id)
    artifact = _validate_external_artifact(session, payload.external_artifact_id, payload.project_id)
    if payload.external_artifact_version_id is not None:
        _validate_external_artifact_version(session, payload.external_artifact_version_id, artifact.id)
    if payload.external_artifact_version_id is None and payload.relation_type in {ArtifactLinkRelationType.validated_against, ArtifactLinkRelationType.synchronized_with}:
        # These relation types are most useful when pinned to a version, but the API does not require it.
        pass
    return _read(ArtifactLinkRead, _add(session, ArtifactLink.model_validate(payload)))

def delete_artifact_link(session: Session, link_id: UUID) -> None:
    item = _get(session, ArtifactLink, link_id)
    if item is None:
        raise LookupError("Artifact link not found")
    session.delete(item)
    session.commit()

__all__ = [
    "list_connectors",
    "create_connector",
    "update_connector",
    "get_connector_service",
    "list_external_artifact_versions",
    "create_external_artifact_version",
    "list_external_artifacts",
    "create_external_artifact",
    "update_external_artifact",
    "get_external_artifact_service",
    "list_artifact_links",
    "create_artifact_link",
    "delete_artifact_link",
]
