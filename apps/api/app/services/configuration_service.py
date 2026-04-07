"""Configuration Service service layer for the DigitalThread API."""

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

def list_configuration_contexts(session: Session, project_id: UUID) -> list[ConfigurationContextRead]:
    rows = _items(session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project_id).order_by(desc(ConfigurationContext.created_at))))
    reads: list[ConfigurationContextRead] = []
    for row in rows:
        read = ConfigurationContextRead.model_validate(row)
        read.item_count = len(_items(session.exec(select(ConfigurationItemMapping).where(ConfigurationItemMapping.configuration_context_id == row.id))))
        reads.append(read)
    return reads

def create_configuration_context(session: Session, payload: ConfigurationContextCreate) -> ConfigurationContextRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    item = _add(session, ConfigurationContext.model_validate(payload))
    _log_action(
        session,
        object_type="configuration_context",
        obj=item,
        from_status=_status_value(item.status),
        to_status=_status_value(item.status),
        action="create",
        actor=None,
        comment=item.description,
    )
    return _read(ConfigurationContextRead, item)

def update_configuration_context(session: Session, obj_id: UUID, payload: ConfigurationContextUpdate) -> ConfigurationContextRead:
    item = _get(session, ConfigurationContext, obj_id)
    if item is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(item)
    before_status = _status_value(item.status)
    before_data = item.model_dump()
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    _commit(session, item)
    if payload.model_dump(exclude_unset=True):
        _log_action(
            session,
            object_type="configuration_context",
            obj=item,
            from_status=before_status,
            to_status=_status_value(item.status),
            action="update",
            actor=None,
            comment=payload.description or payload.name or before_data.get("description"),
        )
    return _read(ConfigurationContextRead, item)

def list_configuration_item_mappings(session: Session, context_id: UUID) -> list[ConfigurationItemMappingRead]:
    rows = _items(
        session.exec(
            select(ConfigurationItemMapping)
            .where(ConfigurationItemMapping.configuration_context_id == context_id)
            .order_by(ConfigurationItemMapping.created_at, ConfigurationItemMapping.id)
        )
    )
    return [ConfigurationItemMappingRead.model_validate(item) for item in rows]

def create_configuration_item_mapping(session: Session, context_id: UUID, payload: ConfigurationItemMappingCreate) -> ConfigurationItemMappingRead:
    context = _get(session, ConfigurationContext, context_id)
    if context is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(context)
    _validate_configuration_mapping(session, context, payload)
    item = ConfigurationItemMapping(configuration_context_id=context_id, **payload.model_dump())
    created = _add(session, item)
    _log_action(
        session,
        object_type="configuration_context",
        obj=context,
        from_status=_status_value(context.status),
        to_status=_status_value(context.status),
        action="add_mapping",
        actor=None,
        comment=payload.role_label or payload.notes,
    )
    return _read(ConfigurationItemMappingRead, created)

def delete_configuration_item_mapping(session: Session, mapping_id: UUID) -> None:
    item = _get(session, ConfigurationItemMapping, mapping_id)
    if item is None:
        raise LookupError("Configuration item mapping not found")
    context = _get(session, ConfigurationContext, item.configuration_context_id)
    if context is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(context)
    _log_action(
        session,
        object_type="configuration_context",
        obj=context,
        from_status=_status_value(context.status),
        to_status=_status_value(context.status),
        action="remove_mapping",
        actor=None,
        comment=item.role_label or item.notes,
    )
    session.delete(item)
    session.commit()

def get_configuration_context_service(session: Session, obj_id: UUID) -> dict[str, Any]:
    context = _get(session, ConfigurationContext, obj_id)
    if context is None:
        raise LookupError("Configuration context not found")
    items = list_configuration_item_mappings(session, obj_id)
    resolved_internal: list[dict[str, Any]] = []
    resolved_external: list[dict[str, Any]] = []
    for item in items:
        if item.internal_object_id is not None and item.internal_object_type is not None:
            internal = _validate_internal_object(session, item.internal_object_type, item.internal_object_id, context.project_id)
            resolved_internal.append(
                {
                    "mapping_id": item.id,
                    "item_kind": item.item_kind.value,
                    "label": internal["label"],
                    "object_type": item.internal_object_type.value,
                    "object_id": str(item.internal_object_id),
                    "version": item.internal_object_version,
                    "role_label": item.role_label,
                    "notes": item.notes,
                }
            )
        if item.external_artifact_version_id is not None:
            version, artifact, connector = _resolve_external_artifact_version_for_project(
                session,
                item.external_artifact_version_id,
                context.project_id,
            )
            resolved_external.append(
                {
                    "mapping_id": item.id,
                    "item_kind": item.item_kind.value,
                    "artifact_name": artifact.name,
                    "artifact_type": artifact.artifact_type.value,
                    "external_artifact_id": str(artifact.id),
                    "external_artifact_version_id": str(version.id),
                    "version_label": version.version_label,
                    "revision_label": version.revision_label,
                    "connector_name": connector.name if connector else None,
                    "role_label": item.role_label,
                    "notes": item.notes,
                }
            )
    resolved_internal.sort(key=lambda item: (item["item_kind"], item["label"], item["object_type"] or "", item["version"] or -1))
    resolved_external.sort(
        key=lambda item: (
            item["item_kind"],
            item["connector_name"] or "",
            item["artifact_name"] or "",
            item["version_label"] or "",
            item["revision_label"] or "",
        )
    )
    related_baselines = _related_baselines_for_configuration_context(session, context)
    return {
        "context": _read(ConfigurationContextRead, context),
        "items": items,
        "resolved_view": {
            "internal": resolved_internal,
            "external": resolved_external,
        },
        "related_baselines": related_baselines,
        "history": list_configuration_context_history(session, obj_id),
    }

def list_configuration_context_history(session: Session, obj_id: UUID) -> list[ApprovalActionLogRead]:
    rows = _items(
        session.exec(
            select(ApprovalActionLog)
            .where(ApprovalActionLog.object_type == "configuration_context", ApprovalActionLog.object_id == obj_id)
            .order_by(desc(ApprovalActionLog.created_at), desc(ApprovalActionLog.id))
        )
    )
    return [ApprovalActionLogRead.model_validate(item) for item in rows]

def compare_configuration_contexts(session: Session, left_context_id: UUID, right_context_id: UUID) -> ConfigurationContextComparisonResponse:
    left_context = _get(session, ConfigurationContext, left_context_id)
    if left_context is None:
        raise LookupError("Configuration context not found")
    right_context = _get(session, ConfigurationContext, right_context_id)
    if right_context is None:
        raise LookupError("Configuration context not found")
    if left_context.project_id != right_context.project_id:
        raise ValueError("Configuration contexts must belong to the same project")

    left_entries = [
        _configuration_context_comparison_entry(session, left_context.project_id, item)
        for item in list_configuration_item_mappings(session, left_context_id)
    ]
    right_entries = [
        _configuration_context_comparison_entry(session, right_context.project_id, item)
        for item in list_configuration_item_mappings(session, right_context_id)
    ]
    groups, summary = _compare_configuration_entry_groups(left_entries, right_entries)

    return ConfigurationContextComparisonResponse(
        left_context=_read(ConfigurationContextRead, left_context),
        right_context=_read(ConfigurationContextRead, right_context),
        summary=summary,
        groups=groups,
    )

def compare_baseline_to_configuration_context(
    session: Session,
    baseline_id: UUID,
    context_id: UUID,
) -> BaselineContextComparisonResponse:
    baseline = _get(session, Baseline, baseline_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    context = _get(session, ConfigurationContext, context_id)
    if context is None:
        raise LookupError("Configuration context not found")
    if baseline.project_id != context.project_id:
        raise ValueError("Baseline and configuration context must belong to the same project")

    baseline_entries = [
        _baseline_comparison_entry(session, baseline.project_id, item)
        for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline_id)))
    ]
    context_entries = [
        _configuration_context_comparison_entry(session, context.project_id, item)
        for item in list_configuration_item_mappings(session, context_id)
    ]
    groups, summary = _compare_configuration_entry_groups(baseline_entries, context_entries)

    return BaselineContextComparisonResponse(
        baseline=_read(BaselineRead, baseline),
        configuration_context=_read(ConfigurationContextRead, context),
        summary=summary,
        groups=groups,
    )

def get_authoritative_registry_summary(session: Session, project_id: UUID) -> AuthoritativeRegistrySummary:
    snapshots = _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project_id)))
    snapshot_groups: dict[tuple[str, UUID], list[RevisionSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        snapshot_groups[(snapshot.object_type, snapshot.object_id)].append(snapshot)

    broken_objects = 0
    issues: list[str] = []
    for (object_type, object_id), rows in snapshot_groups.items():
        rows = sorted(
            rows,
            key=lambda snapshot: (
                snapshot.version,
                snapshot.changed_at or datetime.min.replace(tzinfo=timezone.utc),
                str(snapshot.id),
            ),
        )
        previous_hash: str | None = None
        object_broken = False
        for row in rows:
            expected_hash = _compute_snapshot_hash(
                project_id=row.project_id,
                object_type=row.object_type,
                object_id=row.object_id,
                version=row.version,
                snapshot_json=row.snapshot_json,
                previous_snapshot_hash=previous_hash,
            )
            if row.previous_snapshot_hash != previous_hash:
                object_broken = True
                issues.append(f"{object_type} {object_id}: previous hash mismatch at version {row.version}.")
            if row.snapshot_hash != expected_hash:
                object_broken = True
                issues.append(f"{object_type} {object_id}: snapshot hash mismatch at version {row.version}.")
            previous_hash = row.snapshot_hash
        if object_broken:
            broken_objects += 1

    integrity_status = "warning" if not snapshots else "broken" if broken_objects else "ok"
    return AuthoritativeRegistrySummary(
        connectors=len(_items(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project_id)))),
        external_artifacts=len(_items(session.exec(select(ExternalArtifact).where(ExternalArtifact.project_id == project_id)))),
        external_artifact_versions=len(_items(session.exec(select(ExternalArtifactVersion).join(ExternalArtifact).where(ExternalArtifact.project_id == project_id)))),
        artifact_links=len(_items(session.exec(select(ArtifactLink).where(ArtifactLink.project_id == project_id)))),
        configuration_contexts=len(_items(session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project_id)))),
        configuration_item_mappings=len(_items(session.exec(select(ConfigurationItemMapping).join(ConfigurationContext).where(ConfigurationContext.project_id == project_id)))),
        revision_snapshots=len(snapshots),
        revision_snapshot_objects=len(snapshot_groups),
        revision_snapshot_objects_broken=broken_objects,
        revision_snapshot_integrity_status=integrity_status,
        revision_snapshot_integrity_issues=issues[:10],
    )

__all__ = [
    "list_configuration_contexts",
    "create_configuration_context",
    "update_configuration_context",
    "list_configuration_item_mappings",
    "create_configuration_item_mapping",
    "delete_configuration_item_mapping",
    "get_configuration_context_service",
    "list_configuration_context_history",
    "compare_configuration_contexts",
    "compare_baseline_to_configuration_context",
    "get_authoritative_registry_summary",
]
