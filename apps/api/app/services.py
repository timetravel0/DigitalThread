from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlmodel import Session

from app.models import *
from app.schemas import *

OBJECT_MODELS = {
    "project": Project,
    "requirement": Requirement,
    "block": Block,
    "component": Component,
    "test_case": TestCase,
    "test_run": TestRun,
    "operational_run": OperationalRun,
    "baseline": Baseline,
    "change_request": ChangeRequest,
}


def _add(session: Session, obj: Any) -> Any:
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def _touch(obj: Any) -> None:
    obj.updated_at = utcnow()


def _get(session: Session, model: type[Any], obj_id: UUID) -> Any | None:
    return session.get(model, obj_id)


def _read(model: type[Any], obj: Any) -> Any:
    return model.model_validate(obj)


def _items(result: Any) -> list[Any]:
    items: list[Any] = []
    for row in result:
        if hasattr(row, "id"):
            items.append(row)
        elif hasattr(row, "_mapping") or hasattr(row, "__getitem__"):
            items.append(row[0])
        else:
            items.append(row)
    return items


def _status_value(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _snapshot(session: Session, object_type: str, obj: Any, summary: str | None = None, actor: str | None = None) -> None:
    session.add(
        RevisionSnapshot(
            project_id=obj.project_id,
            object_type=object_type,
            object_id=obj.id,
            version=getattr(obj, "version", 1),
            snapshot_json=obj.model_dump(mode="json"),
            changed_by=actor,
            change_summary=summary,
        )
    )


def _log_action(
    session: Session,
    *,
    object_type: str,
    obj: Any,
    from_status: str,
    to_status: str,
    action: str,
    actor: str | None = None,
    comment: str | None = None,
) -> None:
    session.add(
        ApprovalActionLog(
            project_id=obj.project_id,
            object_type=object_type,
            object_id=obj.id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            actor=actor,
            comment=comment,
        )
    )


def _commit(session: Session, obj: Any) -> Any:
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def _editable(status: Any) -> bool:
    return _status_value(status) in {"draft", "rejected"}


def resolve_object(session: Session, object_type: str, object_id: UUID) -> dict[str, Any]:
    model = OBJECT_MODELS.get(object_type)
    if model is None:
        raise ValueError(f"Unsupported object type: {object_type}")
    obj = _get(session, model, object_id)
    if obj is None:
        raise LookupError(f"{object_type} not found")
    if object_type == "project":
        project_id, label, code, status, version = obj.id, obj.name, obj.code, obj.status, None
    elif object_type == "test_run":
        tc = _get(session, TestCase, obj.test_case_id)
        if tc is None:
            raise LookupError("test_case not found")
        project_id, label, code, status, version = tc.project_id, (obj.summary or f"Test run {obj.id}"), None, obj.result, None
    elif object_type == "block":
        project_id = obj.project_id
        label = obj.name
        code = obj.key
        status = obj.status
        version = obj.version
    else:
        project_id = obj.project_id
        label = getattr(obj, "title", None) or getattr(obj, "name", None) or getattr(obj, "key", None)
        code = getattr(obj, "key", None)
        status = getattr(obj, "status", None)
        version = getattr(obj, "version", None)
    return {
        "object_type": object_type,
        "object_id": obj.id,
        "project_id": project_id,
        "label": label,
        "code": code,
        "status": status.value if hasattr(status, "value") else status,
        "version": version,
        "raw": obj,
    }


def summarize(resolved: dict[str, Any]) -> ObjectSummary:
    return ObjectSummary(
        object_type=resolved["object_type"],
        object_id=resolved["object_id"],
        label=resolved["label"],
        code=resolved["code"],
        status=resolved["status"],
        version=resolved["version"],
    )


def list_projects_service(session: Session) -> list[ProjectRead]:
    return [ProjectRead.model_validate(item) for item in _items(session.exec(select(Project).order_by(Project.code)))]


def get_project_service(session: Session, project_id: UUID) -> ProjectRead:
    item = _get(session, Project, project_id)
    if item is None:
        raise LookupError("Project not found")
    return _read(ProjectRead, item)


def export_project_bundle(session: Session, project_id: UUID) -> dict[str, Any]:
    project = get_project_service(session, project_id)
    bundle = {
        "schema": "threadlite.project.export.v1",
        "exported_at": utcnow().isoformat(),
        "project": project.model_dump(mode="json"),
        "dashboard": get_project_dashboard(session, project_id).model_dump(mode="json"),
        "requirements": [RequirementRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))],
        "blocks": [BlockRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Block).where(Block.project_id == project_id)))],
        "block_containments": [BlockContainmentRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(BlockContainment).where(BlockContainment.project_id == project_id)))],
        "components": [ComponentRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Component).where(Component.project_id == project_id)))],
        "test_cases": [TestCaseRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(TestCase).where(TestCase.project_id == project_id)))],
        "test_runs": [TestRunRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(TestRun).join(TestCase).where(TestCase.project_id == project_id)))],
        "operational_runs": [OperationalRunRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(OperationalRun).where(OperationalRun.project_id == project_id)))],
        "links": [LinkRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(Link).where(Link.project_id == project_id)))],
        "sysml_relations": [SysMLRelationRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id)))],
        "baselines": [
            {
                "baseline": BaselineRead.model_validate(baseline).model_dump(mode="json"),
                "items": [BaselineItemRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline.id)))],
            }
            for baseline in _items(session.exec(select(Baseline).where(Baseline.project_id == project_id)))
        ],
        "change_requests": [ChangeRequestRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "change_impacts": [ChangeImpactRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeImpact).join(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "revision_snapshots": [RevisionSnapshotRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project_id)))],
    }
    return bundle


def create_project(session: Session, payload: ProjectCreate) -> ProjectRead:
    return _read(ProjectRead, _add(session, Project.model_validate(payload)))


def update_project(session: Session, project_id: UUID, payload: ProjectUpdate) -> ProjectRead:
    item = _get(session, Project, project_id)
    if item is None:
        raise LookupError("Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(ProjectRead, _add(session, item))


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


def create_component(session: Session, payload: ComponentCreate) -> ComponentRead:
    return _read(ComponentRead, _add(session, Component.model_validate(payload)))


def update_component(session: Session, obj_id: UUID, payload: ComponentUpdate) -> ComponentRead:
    item = _get(session, Component, obj_id)
    if item is None:
        raise LookupError("Component not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(ComponentRead, _add(session, item))


def list_components(session: Session, project_id: UUID) -> list[ComponentRead]:
    return [ComponentRead.model_validate(item) for item in _items(session.exec(select(Component).where(Component.project_id == project_id).order_by(Component.key)))]


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


def create_sysml_relation(session: Session, payload: SysMLRelationCreate) -> SysMLRelationRead:
    source = resolve_object(session, payload.source_type.value, payload.source_id)
    target = resolve_object(session, payload.target_type.value, payload.target_id)
    if source["project_id"] != target["project_id"] or source["project_id"] != payload.project_id:
        raise ValueError("SysML relations must stay within the same project")
    _validate_sysml_relation_pattern(payload)
    return SysMLRelationRead.model_validate(_add(session, SysMLRelation.model_validate(payload)))


def _validate_sysml_relation_pattern(payload: SysMLRelationCreate) -> None:
    allowed = {
        (SysMLObjectType.block, SysMLObjectType.requirement, SysMLRelationType.satisfy),
        (SysMLObjectType.test_case, SysMLObjectType.requirement, SysMLRelationType.verify),
        (SysMLObjectType.requirement, SysMLObjectType.requirement, SysMLRelationType.deriveReqt),
        (SysMLObjectType.requirement, SysMLObjectType.block, SysMLRelationType.allocate),
        (SysMLObjectType.requirement, SysMLObjectType.block, SysMLRelationType.refine),
        (SysMLObjectType.requirement, SysMLObjectType.block, SysMLRelationType.trace),
        (SysMLObjectType.block, SysMLObjectType.block, SysMLRelationType.contain),
        (SysMLObjectType.block, SysMLObjectType.test_case, SysMLRelationType.trace),
        (SysMLObjectType.requirement, SysMLObjectType.test_case, SysMLRelationType.trace),
        (SysMLObjectType.component, SysMLObjectType.requirement, SysMLRelationType.trace),
        (SysMLObjectType.operational_run, SysMLObjectType.requirement, SysMLRelationType.trace),
    }
    if (payload.source_type, payload.target_type, payload.relation_type) not in allowed:
        raise ValueError("Unsupported SysML relation pattern")


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


def list_review_queue(session: Session, project_id: UUID) -> ReviewQueueResponse:
    project = get_project_service(session, project_id)
    items: list[ReviewQueueItem] = []
    for model, object_type, status_value in (
        (Requirement, "requirement", RequirementStatus.in_review),
        (Block, "block", BlockStatus.in_review),
        (TestCase, "test_case", TestCaseStatus.in_review),
    ):
        rows = _items(session.exec(select(model).where(model.project_id == project_id, model.status == status_value)))
        for row in rows:
            items.append(
                ReviewQueueItem(
                    object_type=object_type,
                    id=row.id,
                    key=row.key,
                    title=getattr(row, "title", getattr(row, "name", "")),
                    status=_status_value(row.status),
                    version=row.version,
                    updated_at=row.updated_at,
                )
            )
    return ReviewQueueResponse(project=project, items=sorted(items, key=lambda item: item.updated_at, reverse=True))


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


def create_baseline(session: Session, payload: BaselineCreate) -> tuple[BaselineRead, list[BaselineItemRead]]:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    baseline = _add(session, Baseline.model_validate(payload))
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


def list_baselines(session: Session, project_id: UUID) -> list[BaselineRead]:
    return [BaselineRead.model_validate(item) for item in _items(session.exec(select(Baseline).where(Baseline.project_id == project_id).order_by(desc(Baseline.created_at))))]


def get_baseline_detail(session: Session, baseline_id: UUID) -> dict[str, Any]:
    baseline = _get(session, Baseline, baseline_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    items = [BaselineItemRead.model_validate(item) for item in _items(session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline_id)))]
    return {"baseline": BaselineRead.model_validate(baseline), "items": items}


def create_change_request(session: Session, payload: ChangeRequestCreate) -> ChangeRequestRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    return _read(ChangeRequestRead, _add(session, ChangeRequest.model_validate(payload)))


def update_change_request(session: Session, obj_id: UUID, payload: ChangeRequestUpdate) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(ChangeRequestRead, _add(session, item))


def list_change_requests(session: Session, project_id: UUID) -> list[ChangeRequestRead]:
    return [ChangeRequestRead.model_validate(item) for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id).order_by(desc(ChangeRequest.created_at))))]


def create_change_impact(session: Session, payload: ChangeImpactCreate) -> ChangeImpactRead:
    if _get(session, ChangeRequest, payload.change_request_id) is None:
        raise LookupError("Change request not found")
    return _read(ChangeImpactRead, _add(session, ChangeImpact.model_validate(payload)))


def list_change_impacts(session: Session, change_request_id: UUID) -> list[ChangeImpactRead]:
    return [ChangeImpactRead.model_validate(item) for item in _items(session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == change_request_id)))]


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


def list_links(session: Session, project_id: UUID, object_type: str | None = None, object_id: UUID | None = None) -> list[LinkRead]:
    stmt = select(Link).where(Link.project_id == project_id)
    if object_type and object_id:
        otype = LinkObjectType(object_type)
        stmt = stmt.where(((Link.source_type == otype) & (Link.source_id == object_id)) | ((Link.target_type == otype) & (Link.target_id == object_id)))
    links = [LinkRead.model_validate(item) for item in _items(session.exec(stmt.order_by(Link.created_at)))]
    for link in links:
        src = resolve_object(session, link.source_type.value, link.source_id)
        tgt = resolve_object(session, link.target_type.value, link.target_id)
        link.source_label = src["label"]
        link.target_label = tgt["label"]
    return links


def _latest_test_run(session: Session, test_case_id: UUID) -> TestRun | None:
    stmt = select(TestRun).where(TestRun.test_case_id == test_case_id).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))
    items = _items(session.exec(stmt))
    return items[0] if items else None


def get_project_dashboard(session: Session, project_id: UUID) -> ProjectDashboard:
    project = get_project_service(session, project_id)
    requirements = _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))
    links = _items(session.exec(select(Link).where(Link.project_id == project_id)))
    test_runs = list_test_runs(session, project_id)
    change_requests = list_change_requests(session, project_id)

    req_components = req_tests = req_risk = 0
    for req in requirements:
        alloc = [l for l in links if l.source_type == LinkObjectType.requirement and l.source_id == req.id and l.relation_type == RelationType.allocated_to and l.target_type == LinkObjectType.component]
        vtests = [l for l in links if l.source_type == LinkObjectType.requirement and l.source_id == req.id and l.relation_type == RelationType.verifies and l.target_type == LinkObjectType.test_case]
        if alloc:
            req_components += 1
        if vtests:
            req_tests += 1
            if any((_latest_test_run(session, l.target_id) and _latest_test_run(session, l.target_id).result == TestRunResult.failed) for l in vtests):
                req_risk += 1

    return ProjectDashboard(
        project=project,
        kpis=DashboardKpis(
            total_requirements=len(requirements),
            requirements_with_allocated_components=req_components,
            requirements_with_verifying_tests=req_tests,
            requirements_at_risk=req_risk,
            failed_tests_last_30_days=len([r for r in test_runs if r.result == TestRunResult.failed and r.execution_date >= date.today() - timedelta(days=30)]),
            open_change_requests=len([cr for cr in change_requests if cr.status == ChangeRequestStatus.open]),
        ),
        recent_test_runs=test_runs[:5],
        recent_changes=change_requests[:5],
        recent_links=list_links(session, project_id)[:5],
    )


def get_global_dashboard(session: Session) -> GlobalDashboard:
    projects = list_projects_service(session)
    all_requirements = _items(session.exec(select(Requirement)))
    all_links = _items(session.exec(select(Link)))
    all_runs = [TestRunRead.model_validate(item) for item in _items(session.exec(select(TestRun).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))))]
    all_changes = [ChangeRequestRead.model_validate(item) for item in _items(session.exec(select(ChangeRequest).order_by(desc(ChangeRequest.created_at))))]
    risk = allocated = verified = 0
    for req in all_requirements:
        req_links = [l for l in all_links if l.source_type == LinkObjectType.requirement and l.source_id == req.id]
        if any(l.relation_type == RelationType.allocated_to and l.target_type == LinkObjectType.component for l in req_links):
            allocated += 1
        verify = [l for l in req_links if l.relation_type == RelationType.verifies and l.target_type == LinkObjectType.test_case]
        if verify:
            verified += 1
            if any((_latest_test_run(session, l.target_id) and _latest_test_run(session, l.target_id).result == TestRunResult.failed) for l in verify):
                risk += 1
    return GlobalDashboard(
        projects=projects,
        kpis=DashboardKpis(
            total_requirements=len(all_requirements),
            requirements_with_allocated_components=allocated,
            requirements_with_verifying_tests=verified,
            requirements_at_risk=risk,
            failed_tests_last_30_days=len([r for r in all_runs if r.result == TestRunResult.failed and r.execution_date >= date.today() - timedelta(days=30)]),
            open_change_requests=len([cr for cr in all_changes if cr.status == ChangeRequestStatus.open]),
        ),
        recent_test_runs=all_runs[:8],
        recent_changes=all_changes[:8],
        recent_links=[LinkRead.model_validate(item) for item in all_links[:8]],
    )


def build_matrix(session: Session, project_id: UUID, mode: str, status: RequirementStatus | None = None, category: RequirementCategory | None = None) -> MatrixResponse:
    project = get_project_service(session, project_id)
    reqs = list_requirements(session, project_id, status=status, category=category)
    if mode == "tests":
        cols = [MatrixColumn(object_type=LinkObjectType.test_case, object_id=item.id, label=item.title, code=item.key, status=item.status.value) for item in list_test_cases(session, project_id)]
        target = LinkObjectType.test_case
    else:
        cols = [MatrixColumn(object_type=LinkObjectType.component, object_id=item.id, label=item.name, code=item.key, status=item.status.value) for item in list_components(session, project_id)]
        target = LinkObjectType.component
    links = _items(session.exec(select(Link).where(Link.project_id == project_id)))
    cells: list[MatrixCell] = []
    for req in reqs:
        for col in cols:
            matches = [l for l in links if l.source_type == LinkObjectType.requirement and l.source_id == req.id and l.target_type == target and l.target_id == col.object_id]
            cells.append(MatrixCell(row_requirement_id=req.id, column_object_type=col.object_type, column_object_id=col.object_id, linked=bool(matches), relation_types=[m.relation_type for m in matches], link_ids=[m.id for m in matches]))
    return MatrixResponse(project=project, mode=mode, requirement_filters={"status": status.value if status else None, "category": category.value if category else None}, rows=[MatrixRow(requirement=req) for req in reqs], columns=cols, cells=cells)


def build_impact(session: Session, project_id: UUID, object_type: str, object_id: UUID) -> ImpactResponse:
    project = get_project_service(session, project_id)
    root = resolve_object(session, object_type, object_id)
    legacy_links = list_links(session, project_id)
    sysml_relations = list_sysml_relations(session, project_id)
    containments = list_block_containments(session, project_id)

    direct: dict[tuple[str, UUID], ObjectSummary] = {}
    secondary: dict[tuple[str, UUID], ObjectSummary] = {}

    def add(bucket: dict[tuple[str, UUID], ObjectSummary], obj: dict[str, Any]) -> None:
        bucket[(obj["object_type"], obj["object_id"])] = summarize(obj)

    if object_type == "block":
        for rel in sysml_relations:
            if rel.relation_type == SysMLRelationType.satisfy and rel.source_type == SysMLObjectType.block and rel.source_id == object_id:
                add(direct, resolve_object(session, "requirement", rel.target_id))
            if rel.relation_type == SysMLRelationType.contain and rel.source_type == SysMLObjectType.block and rel.source_id == object_id:
                add(direct, resolve_object(session, "block", rel.target_id))
        for containment in containments:
            if containment.parent_block_id == object_id:
                add(direct, resolve_object(session, "block", containment.child_block_id))
            elif containment.child_block_id == object_id:
                add(direct, resolve_object(session, "block", containment.parent_block_id))
    elif object_type == "requirement":
        for rel in sysml_relations:
            if rel.source_type == SysMLObjectType.requirement and rel.source_id == object_id and rel.relation_type == SysMLRelationType.deriveReqt:
                add(direct, resolve_object(session, "requirement", rel.target_id))
            if rel.target_type == SysMLObjectType.requirement and rel.target_id == object_id:
                if rel.relation_type == SysMLRelationType.satisfy:
                    add(direct, resolve_object(session, "block", rel.source_id))
                elif rel.relation_type == SysMLRelationType.verify:
                    add(direct, resolve_object(session, "test_case", rel.source_id))
                else:
                    add(direct, resolve_object(session, rel.source_type.value, rel.source_id))
    elif object_type == "test_case":
        for rel in sysml_relations:
            if rel.source_type == SysMLObjectType.test_case and rel.source_id == object_id and rel.relation_type == SysMLRelationType.verify:
                add(direct, resolve_object(session, "requirement", rel.target_id))

    if object_type in {"block", "requirement"}:
        req_ids = [obj.object_id for obj in direct.values() if obj.object_type == "requirement"]
        for req_id in req_ids:
            for rel in _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.test_case, SysMLRelation.target_type == SysMLObjectType.requirement, SysMLRelation.target_id == req_id, SysMLRelation.relation_type == SysMLRelationType.verify))):
                add(secondary, resolve_object(session, "test_case", rel.source_id))
        for rel in _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.requirement, SysMLRelation.target_type == SysMLObjectType.requirement, SysMLRelation.relation_type == SysMLRelationType.deriveReqt, SysMLRelation.source_id.in_(req_ids)))):
            add(secondary, resolve_object(session, "requirement", rel.target_id))

    if object_type == "test_case":
        for rel in sysml_relations:
            if rel.target_type == SysMLObjectType.requirement and rel.relation_type == SysMLRelationType.verify:
                add(secondary, resolve_object(session, "block", rel.source_id))

    for item in list(direct.values()):
        if item.object_type == "requirement":
            for rel in _items(session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project_id, SysMLRelation.source_type == SysMLObjectType.test_case, SysMLRelation.target_type == SysMLObjectType.requirement, SysMLRelation.target_id == item.object_id, SysMLRelation.relation_type == SysMLRelationType.verify))):
                add(secondary, resolve_object(session, "test_case", rel.source_id))
        if item.object_type == "block":
            for containment in containments:
                if containment.parent_block_id == item.object_id:
                    add(secondary, resolve_object(session, "block", containment.child_block_id))
                elif containment.child_block_id == item.object_id:
                    add(secondary, resolve_object(session, "block", containment.parent_block_id))

    likely = {**direct, **secondary}
    related_baselines: list[BaselineRead] = []
    for baseline in list_baselines(session, project_id):
        detail = get_baseline_detail(session, baseline.id)
        baseline_ids = {item.object_id for item in detail["items"]}
        if object_id in baseline_ids or any(obj.object_id in baseline_ids for obj in likely.values()):
            related_baselines.append(baseline)
    open_changes: list[ChangeRequestRead] = []
    for cr in list_change_requests(session, project_id):
        impacts = list_change_impacts(session, cr.id)
        if cr.status == ChangeRequestStatus.open and any(str(impact.object_id) == str(object_id) or any(str(impact.object_id) == str(obj.object_id) for obj in likely.values()) for impact in impacts):
            open_changes.append(cr)

    return ImpactResponse(
        project=project,
        object=summarize(root),
        direct=list(direct.values()),
        secondary=list(secondary.values()),
        likely_impacted=list(likely.values()),
        links=legacy_links,
        related_baselines=related_baselines,
        open_change_requests=open_changes,
    )


def get_requirement_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    return {
        "requirement": RequirementRead.model_validate(item),
        "links": list_links(session, item.project_id, "requirement", item.id),
        "history": list_requirement_history(session, item.id),
        "impact": build_impact(session, item.project_id, "requirement", item.id),
    }


def get_component_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, Component, obj_id)
    if item is None:
        raise LookupError("Component not found")
    impacts = [ChangeImpactRead.model_validate(x) for x in _items(session.exec(select(ChangeImpact).where(ChangeImpact.object_type == "component", ChangeImpact.object_id == obj_id)))]
    return {"component": ComponentRead.model_validate(item), "links": list_links(session, item.project_id, "component", item.id), "impact": build_impact(session, item.project_id, "component", item.id), "change_impacts": impacts}


def get_test_case_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    runs = [TestRunRead.model_validate(x) for x in _items(session.exec(select(TestRun).where(TestRun.test_case_id == obj_id).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))))]
    return {
        "test_case": TestCaseRead.model_validate(item),
        "links": list_links(session, item.project_id, "test_case", item.id),
        "runs": runs,
        "history": list_test_case_history(session, item.id),
        "impact": build_impact(session, item.project_id, "test_case", item.id),
    }


def get_change_request_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    impacts = list_change_impacts(session, obj_id)
    return {"change_request": ChangeRequestRead.model_validate(item), "impacts": impacts, "impact_summary": [summarize(resolve_object(session, x.object_type, x.object_id)) for x in impacts if x.object_type in OBJECT_MODELS]}


def seed_demo(session: Session) -> dict[str, Any]:
    project = session.exec(select(Project).where(Project.code == "DRONE-001")).first()
    if project is None:
        project = _add(session, Project(code="DRONE-001", name="Inspection Drone MVP", description="Demo project for ThreadLite", status=ProjectStatus.active))

    reqs = {}
    for p in [
        {"project_id": project.id, "key": "DR-REQ-001", "title": "Drone shall fly for at least 30 minutes", "description": "Mission endurance target.", "category": RequirementCategory.performance, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-002", "title": "Drone shall stream real-time video to ground operator", "description": "Low latency live video stream.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-003", "title": "Drone shall operate between -5C and 40C", "description": "Environmental envelope.", "category": RequirementCategory.environment, "priority": Priority.high, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-004", "title": "Drone shall detect obstacles during low altitude flight", "description": "Safety obstacle detection.", "category": RequirementCategory.safety, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-005", "title": "Drone shall support remote monitoring of battery and mission status", "description": "Telemetry requirement.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.demonstration, "status": RequirementStatus.draft, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-006", "title": "Battery pack shall support mission reserve margin of 10 percent", "description": "Derived reserve requirement.", "category": RequirementCategory.performance, "priority": Priority.medium, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.draft, "version": 1, "parent_requirement_id": None},
    ]:
        item = _items(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == p["key"])))
        item = item[0] if item else None
        reqs[p["key"]] = item or _add(session, Requirement.model_validate(p))

    if reqs["DR-REQ-006"].parent_requirement_id is None:
        reqs["DR-REQ-006"].parent_requirement_id = reqs["DR-REQ-001"].id
        _touch(reqs["DR-REQ-006"])
        _add(session, reqs["DR-REQ-006"])

    for requirement in reqs.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "requirement", RevisionSnapshot.object_id == requirement.id)).first():
            _snapshot(session, "requirement", requirement, "Seeded requirement", "seed")

    blocks = {}
    for p in [
        {"project_id": project.id, "key": "DR-BLK-001", "name": "Drone System", "description": "Top-level drone system.", "block_kind": BlockKind.system, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-002", "name": "Power Subsystem", "description": "Power distribution and management.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-003", "name": "Propulsion Subsystem", "description": "Lift and propulsion.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-004", "name": "Battery Pack", "description": "High density battery.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-005", "name": "Flight Controller", "description": "Primary flight control unit.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-006", "name": "Camera Module", "description": "Streaming camera.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.draft, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-007", "name": "Obstacle Detection Subsystem", "description": "Obstacle sensing and avoidance.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
    ]:
        item = _items(session.exec(select(Block).where(Block.project_id == project.id, Block.key == p["key"])))
        item = item[0] if item else None
        blocks[p["key"]] = item or _add(session, Block.model_validate(p))

    for block in blocks.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "block", RevisionSnapshot.object_id == block.id)).first():
            _snapshot(session, "block", block, "Seeded block", "seed")

    for parent, child in [
        ("DR-BLK-001", "DR-BLK-002"),
        ("DR-BLK-001", "DR-BLK-003"),
        ("DR-BLK-001", "DR-BLK-005"),
        ("DR-BLK-001", "DR-BLK-006"),
        ("DR-BLK-001", "DR-BLK-007"),
        ("DR-BLK-002", "DR-BLK-004"),
    ]:
        if not session.exec(select(BlockContainment).where(BlockContainment.project_id == project.id, BlockContainment.parent_block_id == blocks[parent].id, BlockContainment.child_block_id == blocks[child].id)).first():
            _add(session, BlockContainment(project_id=project.id, parent_block_id=blocks[parent].id, child_block_id=blocks[child].id, relation_type=BlockContainmentRelationType.contains))

    comps = {}
    for p in [
        {"project_id": project.id, "key": "DR-CMP-001", "name": "Li-Ion Battery Pack", "description": "High density battery.", "type": ComponentType.battery, "part_number": "BAT-3000", "supplier": "VoltCraft", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"capacity_mah": 12000}},
        {"project_id": project.id, "key": "DR-CMP-002", "name": "Brushless Motor Set", "description": "Lift motors.", "type": ComponentType.motor, "part_number": "MTR-2208", "supplier": "AeroSpin", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"kv": 920}},
        {"project_id": project.id, "key": "DR-CMP-003", "name": "Flight Controller", "description": "Primary flight control unit.", "type": ComponentType.flight_controller, "part_number": "FC-REV2", "supplier": "SkyLogic", "status": ComponentStatus.validated, "version": 2, "metadata_json": {"firmware": "1.4.3"}},
        {"project_id": project.id, "key": "DR-CMP-004", "name": "Camera Module", "description": "Streaming camera.", "type": ComponentType.camera, "part_number": "CAM-1080P", "supplier": "OptiView", "status": ComponentStatus.validated, "version": 1, "metadata_json": {"resolution": "1080p"}},
        {"project_id": project.id, "key": "DR-CMP-005", "name": "Obstacle Sensor", "description": "Obstacle detection sensor.", "type": ComponentType.sensor, "part_number": "OBS-LIDAR-1", "supplier": "SenseWorks", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"range_m": 18}},
    ]:
        item = _items(session.exec(select(Component).where(Component.project_id == project.id, Component.key == p["key"])))
        item = item[0] if item else None
        comps[p["key"]] = item or _add(session, Component.model_validate(p))

    tests = {}
    for p in [
        {"project_id": project.id, "key": "DR-TST-001", "title": "Flight Endurance Test", "description": "Validate endurance.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-002", "title": "Video Streaming Test", "description": "Validate video pipeline.", "method": TestMethod.bench, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-003", "title": "Temperature Envelope Test", "description": "Validate temperature range.", "method": TestMethod.simulation, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-004", "title": "Obstacle Detection Test", "description": "Validate obstacle detection.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
    ]:
        item = _items(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == p["key"])))
        item = item[0] if item else None
        tests[p["key"]] = item or _add(session, TestCase.model_validate(p))

    for test_case in tests.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "test_case", RevisionSnapshot.object_id == test_case.id)).first():
            _snapshot(session, "test_case", test_case, "Seeded test case", "seed")

    for rel in [
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery contributes to endurance."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.satisfy, rationale="Flight controller manages video."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-006"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.satisfy, rationale="Camera module provides streaming."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery supports temperature envelope."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.satisfy, rationale="Controller monitors thermal state."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-007"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-004"].id, relation_type=SysMLRelationType.satisfy, rationale="Obstacle subsystem satisfies detection."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-005"].id, relation_type=SysMLRelationType.satisfy, rationale="Controller supports mission monitoring."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-005"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery status reported remotely."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-001"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.verify, rationale="Endurance verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-002"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.verify, rationale="Streaming verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-003"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.verify, rationale="Temperature verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-004"].id, relation_type=SysMLRelationType.verify, rationale="Obstacle detection verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.requirement, source_id=reqs["DR-REQ-006"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.deriveReqt, rationale="Reserve margin derived from endurance."),
    ]:
        if not session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project.id, SysMLRelation.source_type == rel.source_type, SysMLRelation.source_id == rel.source_id, SysMLRelation.target_type == rel.target_type, SysMLRelation.target_id == rel.target_id, SysMLRelation.relation_type == rel.relation_type)).first():
            create_sysml_relation(session, rel)

    for p in [
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-001"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-001"].id, relation_type=RelationType.allocated_to, rationale="Battery contributes to endurance."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-001"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-002"].id, relation_type=RelationType.allocated_to, rationale="Motors influence endurance."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-003"].id, relation_type=RelationType.allocated_to, rationale="Flight controller manages video."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-004"].id, relation_type=RelationType.allocated_to, rationale="Camera module required."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-003"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-001"].id, relation_type=RelationType.allocated_to, rationale="Battery supports temperature envelope."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-003"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-003"].id, relation_type=RelationType.allocated_to, rationale="Controller monitors thermal state."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-004"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-005"].id, relation_type=RelationType.allocated_to, rationale="Obstacle sensor needed."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-005"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-001"].id, relation_type=RelationType.allocated_to, rationale="Battery telemetry exposed remotely."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-005"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-003"].id, relation_type=RelationType.allocated_to, rationale="Controller publishes mission status."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-001"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-001"].id, relation_type=RelationType.verifies, rationale="Endurance test verifies endurance."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-002"].id, relation_type=RelationType.verifies, rationale="Streaming test verifies video."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-003"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-003"].id, relation_type=RelationType.verifies, rationale="Temperature test verifies envelope."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-004"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-004"].id, relation_type=RelationType.verifies, rationale="Obstacle test verifies obstacle detection."),
    ]:
        if not session.exec(select(Link).where(Link.project_id == project.id, Link.source_type == p.source_type, Link.source_id == p.source_id, Link.target_type == p.target_type, Link.target_id == p.target_id, Link.relation_type == p.relation_type)).first():
            _add(session, Link.model_validate(p))

    run = session.exec(select(OperationalRun).where(OperationalRun.project_id == project.id, OperationalRun.key == "DR-RUN-001")).first()
    if run is None:
        run = _add(session, OperationalRun(project_id=project.id, key="DR-RUN-001", date=date.today(), drone_serial="DRN-1001", location="Bologna field test range", duration_minutes=22, max_temperature_c=31.5, battery_consumption_pct=88, outcome=OperationalOutcome.degraded, notes="Mission completed with early low-battery warning.", telemetry_json={"altitude_m": 43, "return_to_home": True}))
    if not session.exec(select(Link).where(Link.project_id == project.id, Link.source_type == LinkObjectType.operational_run, Link.source_id == run.id, Link.target_type == LinkObjectType.requirement, Link.target_id == reqs["DR-REQ-001"].id)).first():
        _add(session, Link(project_id=project.id, source_type=LinkObjectType.operational_run, source_id=run.id, target_type=LinkObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=RelationType.reports_on, rationale="Operational evidence for endurance"))

    for test_key, result, summary, measured in [
        ("DR-TST-001", TestRunResult.failed, "Endurance test failed at 25 minutes.", {"duration_minutes": 25}),
        ("DR-TST-002", TestRunResult.passed, "Streaming test passed.", {"latency_ms": 140}),
        ("DR-TST-003", TestRunResult.passed, "Temperature envelope passed.", {"low_c": -6, "high_c": 41}),
        ("DR-TST-004", TestRunResult.partial, "Obstacle detection partial.", {"detection_rate": 0.84}),
    ]:
        if not session.exec(select(TestRun).join(TestCase).where(TestCase.project_id == project.id, TestCase.key == test_key)).first():
            _add(session, TestRun(test_case_id=tests[test_key].id, execution_date=date.today(), result=result, summary=summary, measured_values_json=measured, notes="Seeded run", executed_by="QA Lead"))

    cr = session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project.id, ChangeRequest.key == "CR-001")).first()
    if cr is None:
        cr = _add(session, ChangeRequest(project_id=project.id, key="CR-001", title="Increase battery endurance to support 35 minutes target", description="Investigate battery and propulsion changes to reach target endurance.", status=ChangeRequestStatus.open, severity=Severity.high))
    if not session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id)).first():
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-001"].id, impact_level=ImpactLevel.high, notes="Battery pack is primary driver."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-002"].id, impact_level=ImpactLevel.medium, notes="Motors influence power draw."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="requirement", object_id=reqs["DR-REQ-001"].id, impact_level=ImpactLevel.high, notes="Endurance requirement needs revision."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="test_case", object_id=tests["DR-TST-001"].id, impact_level=ImpactLevel.medium, notes="Endurance verification test likely changes."))

    baseline = session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Initial Drone Baseline")).first()
    if baseline is None:
        create_baseline(session, BaselineCreate(project_id=project.id, name="Initial Drone Baseline", description="Baseline for the seeded drone MVP."))

    return {"project_id": str(project.id), "seeded": True}
