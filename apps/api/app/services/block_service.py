"""Block Service service layer for the DigitalThread API."""

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
from app.services.link_service import create_sysml_relation, delete_sysml_relation
from app.services.project_service import get_project_service
from app.services.requirement_service import list_requirements
from app.services.test_service import list_test_cases
from app.services.federation_service import list_artifact_links
from app.services.link_service import list_sysml_relations

def create_block(session: Session, payload: BlockCreate) -> BlockRead:
    item = Block.model_validate(payload)
    if item.status == BlockStatus.approved and item.approved_at is None:
        item.approved_at = datetime.now(timezone.utc)
        item.approved_by = "seed"
    _commit(session, item)
    _snapshot(session, "block", item, "Created block")
    return _read(BlockRead, item)

def update_block(session: Session, obj_id: UUID, payload: BlockUpdate) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if not _editable(item.status):
        raise ValueError("Approved and obsolete blocks cannot be edited in place.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    _commit(session, item)
    _snapshot(session, "block", item, "Updated block")
    return _read(BlockRead, item)

def create_block_draft_version(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if item.status != BlockStatus.approved:
        raise ValueError("Draft versions can only be created from approved blocks.")
    released_baselines = _released_baselines_for_object(session, item.project_id, BaselineObjectType.block, item.id)
    if released_baselines:
        _ensure_change_request_for_released_baseline(
            session,
            project_id=item.project_id,
            object_type="block",
            object_id=item.id,
            object_label=f"{item.key} - {item.name}",
            reason=f"Released baseline(s) {', '.join(b.name for b in released_baselines)} include this block and a draft version has been created.",
        )
    draft = Block(
        project_id=item.project_id,
        key=item.key,
        name=item.name,
        description=item.description,
        block_kind=item.block_kind,
        abstraction_level=item.abstraction_level,
        status=BlockStatus.draft,
        version=item.version + 1,
        owner=item.owner,
        review_comment=payload.change_summary if payload else None,
    )
    _commit(session, draft)
    _snapshot(session, "block", draft, "Created draft version", payload.actor if payload else None)
    return _read(BlockRead, draft)

def submit_block_for_review(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if not _editable(item.status):
        raise ValueError("Only draft or rejected blocks can be submitted for review.")
    old = _status_value(item.status)
    item.status = BlockStatus.in_review
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="block", obj=item, from_status=old, to_status="in_review", action="submit_review", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "block", item, "Submitted for review", payload.actor if payload else None)
    return _read(BlockRead, item)

def approve_block(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if item.status != BlockStatus.in_review:
        raise ValueError("Only blocks in review can be approved.")
    old = _status_value(item.status)
    item.status = BlockStatus.approved
    item.approved_at = datetime.now(timezone.utc)
    item.approved_by = payload.actor if payload and payload.actor else "system"
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="block", obj=item, from_status=old, to_status="approved", action="approve", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "block", item, "Approved block", payload.actor if payload else None)
    return _read(BlockRead, item)

def reject_block(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if item.status != BlockStatus.in_review:
        raise ValueError("Only blocks in review can be rejected.")
    old = _status_value(item.status)
    item.status = BlockStatus.rejected
    item.rejection_reason = payload.reason if payload and payload.reason else payload.comment if payload else None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="block", obj=item, from_status=old, to_status="rejected", action="reject", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "block", item, "Rejected block", payload.actor if payload else None)
    return _read(BlockRead, item)

def send_block_back_to_draft(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> BlockRead:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    if item.status not in {BlockStatus.in_review, BlockStatus.rejected}:
        raise ValueError("Only blocks in review or rejected blocks can be sent back to draft.")
    old = _status_value(item.status)
    item.status = BlockStatus.draft
    item.rejection_reason = None
    item.review_comment = payload.comment if payload else item.review_comment
    _touch(item)
    _commit(session, item)
    _log_action(session, object_type="block", obj=item, from_status=old, to_status="draft", action="send_back_to_draft", actor=payload.actor if payload else None, comment=payload.comment if payload else None)
    _snapshot(session, "block", item, "Sent back to draft", payload.actor if payload else None)
    return _read(BlockRead, item)

def list_blocks(session: Session, project_id: UUID) -> list[BlockRead]:
    return [BlockRead.model_validate(item) for item in _items(session.exec(select(Block).where(Block.project_id == project_id).order_by(Block.key)))]

def get_block_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, Block, obj_id)
    if item is None:
        raise LookupError("Block not found")
    return {
        "block": BlockRead.model_validate(item),
        "containments": list_block_containments(session, item.project_id, obj_id=item.id),
        "links": list_sysml_relations(session, item.project_id, object_type="block", object_id=item.id),
        "artifact_links": list_artifact_links(session, item.project_id, internal_object_type=FederatedInternalObjectType.block, internal_object_id=item.id),
        "history": list_block_history(session, item.id),
        "impact": build_impact(session, item.project_id, "block", item.id),
    }

def list_block_history(session: Session, obj_id: UUID) -> list[RevisionSnapshotRead]:
    rows = _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.object_type == "block", RevisionSnapshot.object_id == obj_id).order_by(desc(RevisionSnapshot.changed_at))))
    return [RevisionSnapshotRead.model_validate(item) for item in rows]

def create_block_containment(session: Session, payload: BlockContainmentCreate) -> BlockContainmentRead:
    parent = _get(session, Block, payload.parent_block_id)
    child = _get(session, Block, payload.child_block_id)
    if parent is None or child is None:
        raise LookupError("Block not found")
    if parent.project_id != payload.project_id or child.project_id != payload.project_id:
        raise ValueError("Containment must stay within the same project")
    existing = session.exec(select(BlockContainment).where(BlockContainment.project_id == payload.project_id, BlockContainment.parent_block_id == payload.parent_block_id, BlockContainment.child_block_id == payload.child_block_id)).first()
    if existing:
        return BlockContainmentRead.model_validate(existing)
    return BlockContainmentRead.model_validate(_add(session, BlockContainment.model_validate(payload)))

def delete_block_containment(session: Session, containment_id: UUID) -> None:
    item = _get(session, BlockContainment, containment_id)
    if item is None:
        raise LookupError("Block containment not found")
    session.delete(item)
    session.commit()

def list_block_containments(session: Session, project_id: UUID, obj_id: UUID | None = None) -> list[BlockContainmentRead]:
    stmt = select(BlockContainment).where(BlockContainment.project_id == project_id)
    if obj_id:
        stmt = stmt.where(or_(BlockContainment.parent_block_id == obj_id, BlockContainment.child_block_id == obj_id))
    return [BlockContainmentRead.model_validate(item) for item in _items(session.exec(stmt.order_by(BlockContainment.created_at)))]

def build_block_tree(session: Session, project_id: UUID) -> SysMLTreeResponse:
    project = get_project_service(session, project_id)
    blocks = list_blocks(session, project_id)
    containments = list_block_containments(session, project_id)
    relations = list_sysml_relations(session, project_id)
    nodes = {block.id: BlockTreeNode(block=block) for block in blocks}
    children: dict[UUID, list[UUID]] = {}
    parent_ids: set[UUID] = set()
    satisfied: dict[UUID, list[ObjectSummary]] = defaultdict(list)
    tests_by_req: dict[UUID, list[ObjectSummary]] = defaultdict(list)
    for containment in containments:
        children.setdefault(containment.parent_block_id, []).append(containment.child_block_id)
        parent_ids.add(containment.child_block_id)
    for rel in relations:
        if rel.relation_type == SysMLRelationType.satisfy and rel.source_type == SysMLObjectType.block and rel.target_type == SysMLObjectType.requirement:
            satisfied[rel.source_id].append(summarize(resolve_object(session, "requirement", rel.target_id)))
        if rel.relation_type == SysMLRelationType.verify and rel.source_type == SysMLObjectType.test_case and rel.target_type == SysMLObjectType.requirement:
            tests_by_req[rel.target_id].append(summarize(resolve_object(session, "test_case", rel.source_id)))
    for block in blocks:
        node = nodes[block.id]
        node.satisfied_requirements = satisfied.get(block.id, [])
        test_map: dict[UUID, ObjectSummary] = {}
        for req in node.satisfied_requirements:
            for test in tests_by_req.get(req.object_id, []):
                test_map[test.object_id] = test
        node.linked_tests = list(test_map.values())
    for parent_id, child_ids in children.items():
        nodes[parent_id].children = [nodes[cid] for cid in child_ids if cid in nodes]
    roots = [node for bid, node in nodes.items() if bid not in parent_ids]
    return SysMLTreeResponse(project=project, roots=roots)

def build_satisfaction_view(session: Session, project_id: UUID) -> SysMLSatisfactionResponse:
    project = get_project_service(session, project_id)
    rows: list[SatisfactionRow] = []
    for block in list_blocks(session, project_id):
        rels = _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.block, SysMLRelation.source_id == block.id, SysMLRelation.relation_type == SysMLRelationType.satisfy)))
        rows.append(SatisfactionRow(block=block, requirements=[summarize(resolve_object(session, "requirement", rel.target_id)) for rel in rels]))
    return SysMLSatisfactionResponse(project=project, rows=rows)

def build_verification_view(session: Session, project_id: UUID) -> SysMLVerificationResponse:
    project = get_project_service(session, project_id)
    rows: list[VerificationRow] = []
    for test in list_test_cases(session, project_id):
        rels = _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.test_case, SysMLRelation.source_id == test.id, SysMLRelation.relation_type == SysMLRelationType.verify)))
        rows.append(VerificationRow(test_case=test, requirements=[summarize(resolve_object(session, "requirement", rel.target_id)) for rel in rels]))
    return SysMLVerificationResponse(project=project, rows=rows)

def build_derivation_view(session: Session, project_id: UUID) -> SysMLDerivationResponse:
    project = get_project_service(session, project_id)
    rows: list[DerivationRow] = []
    for req in list_requirements(session, project_id):
        rels = _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.requirement, SysMLRelation.source_id == req.id, SysMLRelation.relation_type == SysMLRelationType.deriveReqt)))
        if rels:
            rows.append(DerivationRow(source_requirement=req, derived_requirements=[summarize(resolve_object(session, "requirement", rel.target_id)) for rel in rels]))
    return SysMLDerivationResponse(project=project, rows=rows)

__all__ = [
    "create_block",
    "update_block",
    "create_block_draft_version",
    "submit_block_for_review",
    "approve_block",
    "reject_block",
    "send_block_back_to_draft",
    "list_blocks",
    "get_block_detail",
    "list_block_history",
    "create_block_containment",
    "delete_block_containment",
    "list_block_containments",
    "build_block_tree",
    "build_satisfaction_view",
    "build_verification_view",
    "build_derivation_view",
]
