from __future__ import annotations

from collections import defaultdict, deque
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
    "non_conformity": NonConformity,
    "verification_evidence": VerificationEvidence,
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


def _utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _impact_node_key(object_type: str, object_id: UUID) -> tuple[str, UUID]:
    return object_type, object_id


def _impact_context_internal_ids(session: Session, project_id: UUID) -> set[UUID]:
    rows = _items(
        session.exec(
            select(ConfigurationContext)
            .where(
                ConfigurationContext.project_id == project_id,
                ConfigurationContext.status != ConfigurationContextStatus.obsolete,
            )
            .order_by(desc(ConfigurationContext.created_at))
        )
    )
    if not rows:
        return set()
    precedence = {
        ConfigurationContextStatus.active: 0,
        ConfigurationContextStatus.frozen: 1,
        ConfigurationContextStatus.draft: 2,
        ConfigurationContextStatus.obsolete: 3,
    }
    context = sorted(rows, key=lambda item: (precedence[item.status], item.updated_at, item.created_at))[0]
    mappings = _items(
        session.exec(
            select(ConfigurationItemMapping).where(
                ConfigurationItemMapping.configuration_context_id == context.id,
                ConfigurationItemMapping.internal_object_id.is_not(None),
            )
        )
    )
    return {mapping.internal_object_id for mapping in mappings if mapping.internal_object_id is not None}


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
    elif object_type == "verification_evidence":
        project_id = obj.project_id
        label = obj.title
        code = obj.source_reference or obj.source_name
        status = obj.evidence_type
        version = None
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


def _validate_internal_object(session: Session, object_type: FederatedInternalObjectType, object_id: UUID, project_id: UUID) -> dict[str, Any]:
    resolved = resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Referenced internal object must stay within the same project")
    return resolved


def _validate_external_artifact(session: Session, artifact_id: UUID, project_id: UUID) -> ExternalArtifact:
    artifact = _get(session, ExternalArtifact, artifact_id)
    if artifact is None:
        raise LookupError("External artifact not found")
    if artifact.project_id != project_id:
        raise ValueError("Referenced external artifact must stay within the same project")
    return artifact


def _validate_external_artifact_version(session: Session, version_id: UUID, artifact_id: UUID) -> ExternalArtifactVersion:
    version = _get(session, ExternalArtifactVersion, version_id)
    if version is None:
        raise LookupError("External artifact version not found")
    if version.external_artifact_id != artifact_id:
        raise ValueError("External artifact version does not belong to the selected artifact")
    return version


def _resolve_external_artifact_version_for_project(
    session: Session,
    version_id: UUID,
    project_id: UUID,
) -> tuple[ExternalArtifactVersion, ExternalArtifact, ConnectorDefinition | None]:
    version = _get(session, ExternalArtifactVersion, version_id)
    if version is None:
        raise LookupError("External artifact version not found")
    artifact = _validate_external_artifact(session, version.external_artifact_id, project_id)
    connector = _get(session, ConnectorDefinition, artifact.connector_definition_id) if artifact.connector_definition_id else None
    return version, artifact, connector


def _ensure_configuration_context_mutable(context: ConfigurationContext) -> None:
    if (
        context.status in {ConfigurationContextStatus.frozen, ConfigurationContextStatus.obsolete}
        or context.context_type == ConfigurationContextType.released
    ):
        raise ValueError("Frozen, released, or obsolete configuration contexts cannot be modified")


def _artifact_read(session: Session, artifact: ExternalArtifact) -> ExternalArtifactRead:
    read = ExternalArtifactRead.model_validate(artifact)
    connector = _get(session, ConnectorDefinition, artifact.connector_definition_id) if artifact.connector_definition_id else None
    read.connector_name = connector.name if connector else None
    read.connector_type = connector.connector_type if connector else None
    read.versions = list_external_artifact_versions(session, artifact.id)
    return read


def _connector_read(session: Session, connector: ConnectorDefinition) -> ConnectorDefinitionRead:
    read = ConnectorDefinitionRead.model_validate(connector)
    read.artifact_count = len(_items(session.exec(select(ExternalArtifact).where(ExternalArtifact.connector_definition_id == connector.id))))
    return read


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


def _resolve_artifact_link_internal_label(session: Session, link: ArtifactLink) -> str:
    resolved = resolve_object(session, link.internal_object_type.value, link.internal_object_id)
    return resolved["label"]


def _resolve_artifact_link_external_label(session: Session, link: ArtifactLink) -> tuple[str, str | None, str | None]:
    artifact = _get(session, ExternalArtifact, link.external_artifact_id)
    if artifact is None:
        raise LookupError("External artifact not found")
    connector = _get(session, ConnectorDefinition, artifact.connector_definition_id) if artifact.connector_definition_id else None
    version_label = None
    if link.external_artifact_version_id:
        version = _get(session, ExternalArtifactVersion, link.external_artifact_version_id)
        if version is None:
            raise LookupError("External artifact version not found")
        version_label = version.version_label
    return artifact.name, version_label, connector.name if connector else None


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
    return _read(ConfigurationContextRead, _add(session, ConfigurationContext.model_validate(payload)))


def update_configuration_context(session: Session, obj_id: UUID, payload: ConfigurationContextUpdate) -> ConfigurationContextRead:
    item = _get(session, ConfigurationContext, obj_id)
    if item is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(item)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(ConfigurationContextRead, _add(session, item))


def list_configuration_item_mappings(session: Session, context_id: UUID) -> list[ConfigurationItemMappingRead]:
    rows = _items(
        session.exec(
            select(ConfigurationItemMapping)
            .where(ConfigurationItemMapping.configuration_context_id == context_id)
            .order_by(ConfigurationItemMapping.created_at, ConfigurationItemMapping.id)
        )
    )
    return [ConfigurationItemMappingRead.model_validate(item) for item in rows]


def _validate_configuration_mapping(session: Session, context: ConfigurationContext, payload: ConfigurationItemMappingCreate) -> None:
    if payload.internal_object_id is None and payload.external_artifact_version_id is None:
        raise ValueError("Configuration item mapping must reference at least one concrete item")
    if payload.internal_object_id is not None:
        if payload.internal_object_type is None or payload.internal_object_version is None:
            raise ValueError("Internal configuration mappings require object type and object version")
        resolved = _validate_internal_object(session, payload.internal_object_type, payload.internal_object_id, context.project_id)
        if resolved["version"] is not None and payload.internal_object_version != resolved["version"]:
            raise ValueError("Internal object version does not match the selected object")
    if payload.external_artifact_version_id is not None:
        _resolve_external_artifact_version_for_project(session, payload.external_artifact_version_id, context.project_id)


def create_configuration_item_mapping(session: Session, context_id: UUID, payload: ConfigurationItemMappingCreate) -> ConfigurationItemMappingRead:
    context = _get(session, ConfigurationContext, context_id)
    if context is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(context)
    _validate_configuration_mapping(session, context, payload)
    item = ConfigurationItemMapping(configuration_context_id=context_id, **payload.model_dump())
    return _read(ConfigurationItemMappingRead, _add(session, item))


def delete_configuration_item_mapping(session: Session, mapping_id: UUID) -> None:
    item = _get(session, ConfigurationItemMapping, mapping_id)
    if item is None:
        raise LookupError("Configuration item mapping not found")
    context = _get(session, ConfigurationContext, item.configuration_context_id)
    if context is None:
        raise LookupError("Configuration context not found")
    _ensure_configuration_context_mutable(context)
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
    }


def _configuration_context_comparison_entry(
    session: Session,
    context_project_id: UUID,
    item: ConfigurationItemMappingRead,
) -> dict[str, Any]:
    if item.internal_object_id is not None and item.internal_object_type is not None:
        internal = _validate_internal_object(session, item.internal_object_type, item.internal_object_id, context_project_id)
        object_code = internal.get("code") or str(item.internal_object_id)
        return {
            "item_kind": item.item_kind,
            "key": f"{item.item_kind.value}:{item.internal_object_type.value}:{object_code}",
            "signature": item.internal_object_version,
            "entry": ConfigurationContextComparisonEntry(
                item_kind=item.item_kind,
                label=f"{object_code} - {internal['label']}" if internal.get("code") else internal["label"],
                object_type=item.internal_object_type.value,
                object_id=item.internal_object_id,
                object_version=item.internal_object_version,
                role_label=item.role_label,
                notes=item.notes,
            ),
        }
    if item.external_artifact_version_id is not None:
        version, artifact, connector = _resolve_external_artifact_version_for_project(
            session,
            item.external_artifact_version_id,
            context_project_id,
        )
        return {
            "item_kind": item.item_kind,
            "key": f"{item.item_kind.value}:external:{artifact.id}",
            "signature": str(version.id),
            "entry": ConfigurationContextComparisonEntry(
                item_kind=item.item_kind,
                label=f"{artifact.external_id} - {artifact.name}",
                external_artifact_id=artifact.id,
                external_artifact_version_id=version.id,
                version_label=version.version_label,
                revision_label=version.revision_label,
                connector_name=connector.name if connector else None,
                artifact_name=artifact.name,
                artifact_type=artifact.artifact_type.value,
                role_label=item.role_label,
                notes=item.notes,
            ),
        }
    raise ValueError("Configuration item mapping is missing a concrete object reference")

def _baseline_comparison_entry(session: Session, baseline_project_id: UUID, item: BaselineItemRead) -> dict[str, Any]:
    internal_object_type = FederatedInternalObjectType(item.object_type.value)
    internal = _validate_internal_object(session, internal_object_type, item.object_id, baseline_project_id)
    object_code = internal.get("code") or str(item.object_id)
    item_kind = {
        BaselineObjectType.requirement: ConfigurationItemKind.internal_requirement,
        BaselineObjectType.block: ConfigurationItemKind.internal_block,
        BaselineObjectType.test_case: ConfigurationItemKind.internal_test_case,
        BaselineObjectType.component: ConfigurationItemKind.baseline_item,
    }[item.object_type]
    return {
        "item_kind": item_kind,
        "key": f"{item_kind.value}:{item.object_type.value}:{object_code}",
        "signature": item.object_version,
        "entry": ConfigurationContextComparisonEntry(
            item_kind=item_kind,
            label=f"{object_code} - {internal['label']}" if internal.get("code") else internal["label"],
            object_type=item.object_type.value,
            object_id=item.object_id,
            object_version=item.object_version,
        ),
    }


def _compare_configuration_entry_groups(
    left_entries: list[dict[str, Any]],
    right_entries: list[dict[str, Any]],
) -> tuple[list[ConfigurationContextComparisonGroup], ConfigurationContextComparisonSummary]:
    grouped_left: dict[ConfigurationItemKind, dict[str, dict[str, Any]]] = defaultdict(dict)
    grouped_right: dict[ConfigurationItemKind, dict[str, dict[str, Any]]] = defaultdict(dict)

    for item in left_entries:
        grouped_left[item["item_kind"]][item["key"]] = item
    for item in right_entries:
        grouped_right[item["item_kind"]][item["key"]] = item

    order = {kind: index for index, kind in enumerate(ConfigurationItemKind)}
    groups: list[ConfigurationContextComparisonGroup] = []
    summary = ConfigurationContextComparisonSummary()

    for item_kind in sorted(set(grouped_left) | set(grouped_right), key=lambda kind: order[kind]):
        left_group = grouped_left.get(item_kind, {})
        right_group = grouped_right.get(item_kind, {})
        added: list[ConfigurationContextComparisonEntry] = []
        removed: list[ConfigurationContextComparisonEntry] = []
        version_changed: list[ConfigurationContextComparisonChange] = []

        for key in sorted(right_group.keys() - left_group.keys()):
            added.append(right_group[key]["entry"])
        for key in sorted(left_group.keys() - right_group.keys()):
            removed.append(left_group[key]["entry"])
        for key in sorted(left_group.keys() & right_group.keys()):
            left_entry = left_group[key]
            right_entry = right_group[key]
            if left_entry["signature"] != right_entry["signature"]:
                version_changed.append(
                    ConfigurationContextComparisonChange(
                        key=key,
                        left=left_entry["entry"],
                        right=right_entry["entry"],
                    )
                )

        if added or removed or version_changed:
            added.sort(key=lambda entry: (entry.label, entry.object_type or "", str(entry.object_id or entry.external_artifact_version_id or "")))
            removed.sort(key=lambda entry: (entry.label, entry.object_type or "", str(entry.object_id or entry.external_artifact_version_id or "")))
            version_changed.sort(
                key=lambda change: (
                    change.left.label if change.left else "",
                    change.right.label if change.right else "",
                    change.key,
                )
            )
            summary.added += len(added)
            summary.removed += len(removed)
            summary.version_changed += len(version_changed)
            groups.append(
                ConfigurationContextComparisonGroup(
                    item_kind=item_kind,
                    added=added,
                    removed=removed,
                    version_changed=version_changed,
                )
            )

    return groups, summary


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


def get_authoritative_registry_summary(session: Session, project_id: UUID) -> AuthoritativeRegistrySummary:
    return AuthoritativeRegistrySummary(
        connectors=len(_items(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project_id)))),
        external_artifacts=len(_items(session.exec(select(ExternalArtifact).where(ExternalArtifact.project_id == project_id)))),
        external_artifact_versions=len(_items(session.exec(select(ExternalArtifactVersion).join(ExternalArtifact).where(ExternalArtifact.project_id == project_id)))),
        artifact_links=len(_items(session.exec(select(ArtifactLink).where(ArtifactLink.project_id == project_id)))),
        configuration_contexts=len(_items(session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project_id)))),
        configuration_item_mappings=len(_items(session.exec(select(ConfigurationItemMapping).join(ConfigurationContext).where(ConfigurationContext.project_id == project_id)))),
    )


def export_project_bundle(session: Session, project_id: UUID) -> dict[str, Any]:
    project = get_project_service(session, project_id)
    connectors = list_connectors(session, project_id)
    external_artifacts = list_external_artifacts(session, project_id)
    external_artifact_versions = [
        ExternalArtifactVersionRead.model_validate(item)
        for item in _items(
            session.exec(
                select(ExternalArtifactVersion)
                .join(ExternalArtifact)
                .where(ExternalArtifact.project_id == project_id)
                .order_by(desc(ExternalArtifactVersion.created_at))
            )
        )
    ]
    artifact_links = list_artifact_links(session, project_id)
    verification_evidence = list_verification_evidence(session, project_id)
    configuration_contexts = list_configuration_contexts(session, project_id)
    configuration_item_mappings = [
        ConfigurationItemMappingRead.model_validate(item)
        for item in _items(
            session.exec(
                select(ConfigurationItemMapping)
                .join(ConfigurationContext)
                .where(ConfigurationContext.project_id == project_id)
                .order_by(ConfigurationItemMapping.created_at)
            )
        )
    ]
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
        "non_conformities": [NonConformityRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id)))],
        "verification_evidence": [evidence.model_dump(mode="json") for evidence in verification_evidence],
        "change_requests": [ChangeRequestRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "change_impacts": [ChangeImpactRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeImpact).join(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "revision_snapshots": [RevisionSnapshotRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project_id)))],
        "connectors": [connector.model_dump(mode="json") for connector in connectors],
        "external_artifacts": [artifact.model_dump(mode="json") for artifact in external_artifacts],
        "external_artifact_versions": [version.model_dump(mode="json") for version in external_artifact_versions],
        "artifact_links": [link.model_dump(mode="json") for link in artifact_links],
        "configuration_contexts": [context.model_dump(mode="json") for context in configuration_contexts],
        "configuration_item_mappings": [mapping.model_dump(mode="json") for mapping in configuration_item_mappings],
        "authoritative_registry_summary": get_authoritative_registry_summary(session, project_id).model_dump(mode="json"),
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


def get_operational_run_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, OperationalRun, obj_id)
    if item is None:
        raise LookupError("Operational run not found")
    return {
        "operational_run": OperationalRunRead.model_validate(item),
        "links": list_links(session, item.project_id, "operational_run", item.id),
        "impact": build_impact(session, item.project_id, "operational_run", item.id),
    }


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
    }


def get_baseline_bridge_context(session: Session, baseline_id: UUID) -> BaselineBridgeContextRead:
    detail = get_baseline_detail(session, baseline_id)
    return detail["bridge_context"]


def _related_baselines_for_configuration_context(session: Session, context: ConfigurationContext) -> list[BaselineRead]:
    context_signatures = {
        (item.internal_object_type.value, item.internal_object_id, item.internal_object_version)
        for item in list_configuration_item_mappings(session, context.id)
        if item.internal_object_id is not None and item.internal_object_type is not None and item.internal_object_version is not None
    }
    if not context_signatures:
        return []
    related: list[BaselineRead] = []
    for baseline in list_baselines(session, context.project_id):
        detail = get_baseline_detail(session, baseline.id)
        baseline_items = detail["items"]
        baseline_signature = {(item.object_type.value, item.object_id, item.object_version) for item in baseline_items}
        if baseline_signature and baseline_signature.issubset(context_signatures):
            related.append(baseline)
    return related


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
    rows = _items(
        session.exec(
            select(ApprovalActionLog)
            .where(ApprovalActionLog.object_type == "change_request", ApprovalActionLog.object_id == obj_id)
            .order_by(ApprovalActionLog.created_at, ApprovalActionLog.id)
        )
    )
    return [ApprovalActionLogRead.model_validate(item) for item in rows]


def submit_change_request_for_analysis(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status not in {ChangeRequestStatus.open, ChangeRequestStatus.rejected}:
        raise ValueError("Only open or rejected change requests can move to analysis.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.analysis
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


def create_non_conformity(session: Session, payload: NonConformityCreate) -> NonConformityRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    return _read(NonConformityRead, _add(session, NonConformity.model_validate(payload)))


def update_non_conformity(session: Session, obj_id: UUID, payload: NonConformityUpdate) -> NonConformityRead:
    item = _get(session, NonConformity, obj_id)
    if item is None:
        raise LookupError("Non-conformity not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(NonConformityRead, _add(session, item))


def list_non_conformities(session: Session, project_id: UUID) -> list[NonConformityRead]:
    return [NonConformityRead.model_validate(item) for item in _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id).order_by(desc(NonConformity.created_at))))]


def get_non_conformity_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, NonConformity, obj_id)
    if item is None:
        raise LookupError("Non-conformity not found")
    impacts = list_links(session, item.project_id, "non_conformity", item.id)
    return {
        "non_conformity": NonConformityRead.model_validate(item),
        "links": impacts,
        "verification_evidence": list_verification_evidence(session, item.project_id, internal_object_type=FederatedInternalObjectType.non_conformity, internal_object_id=item.id),
        "impact": build_impact(session, item.project_id, "non_conformity", item.id),
        "impact_summary": [summarize(resolve_object(session, x.object_type, x.object_id)) for x in impacts if x.object_type in OBJECT_MODELS],
    }


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
        if alloc:
            req_components += 1
        evaluation = _evaluate_requirement_verification(session, req)
        if evaluation.status != RequirementVerificationStatus.not_covered:
            req_tests += 1
        if evaluation.status in {RequirementVerificationStatus.at_risk, RequirementVerificationStatus.failed}:
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
        evaluation = _evaluate_requirement_verification(session, req)
        if evaluation.status != RequirementVerificationStatus.not_covered:
            verified += 1
        if evaluation.status in {RequirementVerificationStatus.at_risk, RequirementVerificationStatus.failed}:
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
    root_key = _impact_node_key(object_type, object_id)
    legacy_links = list_links(session, project_id)
    sysml_relations = list_sysml_relations(session, project_id)
    containments = list_block_containments(session, project_id)
    active_context_internal_ids = _impact_context_internal_ids(session, project_id)

    adjacency: dict[tuple[str, UUID], set[tuple[str, UUID]]] = defaultdict(set)
    resolved_nodes: dict[tuple[str, UUID], dict[str, Any]] = {root_key: root}

    def resolve_or_cache(node_type: str, node_id: UUID) -> dict[str, Any]:
        key = _impact_node_key(node_type, node_id)
        if key not in resolved_nodes:
            resolved_nodes[key] = resolve_object(session, node_type, node_id)
        return resolved_nodes[key]

    def add_edge(source_type: str, source_id: UUID, target_type: str, target_id: UUID) -> None:
        source_key = _impact_node_key(source_type, source_id)
        target_key = _impact_node_key(target_type, target_id)
        adjacency[source_key].add(target_key)
        adjacency[target_key].add(source_key)

    for link in legacy_links:
        add_edge(link.source_type.value, link.source_id, link.target_type.value, link.target_id)

    for rel in sysml_relations:
        add_edge(rel.source_type.value, rel.source_id, rel.target_type.value, rel.target_id)

    for containment in containments:
        add_edge("block", containment.parent_block_id, "block", containment.child_block_id)

    evidence_rows = _items(
        session.exec(
            select(VerificationEvidence)
            .where(VerificationEvidence.project_id == project_id)
            .order_by(desc(VerificationEvidence.created_at), desc(VerificationEvidence.updated_at))
        )
    )
    evidence_links = (
        _items(
            session.exec(
                select(VerificationEvidenceLink)
                .where(VerificationEvidenceLink.verification_evidence_id.in_([row.id for row in evidence_rows]))
                .order_by(VerificationEvidenceLink.created_at, VerificationEvidenceLink.id)
            )
        )
        if evidence_rows
        else []
    )
    evidence_links_by_evidence: dict[UUID, list[VerificationEvidenceLink]] = defaultdict(list)
    for link in evidence_links:
        evidence_links_by_evidence[link.verification_evidence_id].append(link)
    for evidence in evidence_rows:
        linked_ids = {
            link.internal_object_id
            for link in evidence_links_by_evidence.get(evidence.id, [])
            if link.internal_object_id is not None
        }
        if active_context_internal_ids and not linked_ids.intersection(active_context_internal_ids):
            continue
        for link in evidence_links_by_evidence.get(evidence.id, []):
            if link.internal_object_id is None:
                continue
            add_edge("verification_evidence", evidence.id, link.internal_object_type.value, link.internal_object_id)

    baseline_items = _items(session.exec(select(BaselineItem).join(Baseline).where(Baseline.project_id == project_id)))
    for item in baseline_items:
        add_edge("baseline", item.baseline_id, item.object_type.value, item.object_id)

    change_impacts = _items(session.exec(select(ChangeImpact).join(ChangeRequest).where(ChangeRequest.project_id == project_id)))
    for impact in change_impacts:
        try:
            add_edge("change_request", impact.change_request_id, impact.object_type, impact.object_id)
        except (LookupError, ValueError):
            continue

    distances: dict[tuple[str, UUID], int] = {root_key: 0}
    queue: deque[tuple[str, UUID]] = deque([root_key])
    while queue:
        current = queue.popleft()
        current_distance = distances[current]
        for neighbor in adjacency.get(current, set()):
            if neighbor in distances:
                continue
            distances[neighbor] = current_distance + 1
            resolve_or_cache(neighbor[0], neighbor[1])
            queue.append(neighbor)

    def sort_summary(item: ObjectSummary) -> tuple[str, str, str]:
        return (item.object_type, item.code or "", item.label or "")

    ranked_impacts = [
        (distance, summarize(resolved_nodes[key]))
        for key, distance in distances.items()
        if key != root_key and distance >= 1
    ]
    ranked_impacts.sort(key=lambda item: (item[0], sort_summary(item[1])))
    direct = [item for distance, item in ranked_impacts if distance == 1]
    secondary = [item for distance, item in ranked_impacts if distance == 2]
    likely = [item for _, item in ranked_impacts]

    related_baseline_ids = sorted(
        {
            key[1]
            for key, distance in distances.items()
            if key[0] == "baseline" and distance >= 1
        },
        key=str,
    )
    related_baselines = [
        _read(BaselineRead, _get(session, Baseline, baseline_id))
        for baseline_id in related_baseline_ids
        if _get(session, Baseline, baseline_id) is not None
    ]
    related_baselines.sort(key=lambda item: (item.name, str(item.id)))

    open_change_request_ids = sorted(
        {
            key[1]
            for key, distance in distances.items()
            if key[0] == "change_request" and distance >= 1
        },
        key=str,
    )
    open_changes = [
        _read(ChangeRequestRead, _get(session, ChangeRequest, change_request_id))
        for change_request_id in open_change_request_ids
        if _get(session, ChangeRequest, change_request_id) is not None and _get(session, ChangeRequest, change_request_id).status == ChangeRequestStatus.open
    ]
    open_changes.sort(key=lambda item: (item.title, str(item.id)))

    return ImpactResponse(
        project=project,
        object=summarize(root),
        direct=direct,
        secondary=secondary,
        likely_impacted=likely,
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
        "artifact_links": list_artifact_links(session, item.project_id, internal_object_type=FederatedInternalObjectType.requirement, internal_object_id=item.id),
        "verification_evidence": list_verification_evidence(session, item.project_id, internal_object_type=FederatedInternalObjectType.requirement, internal_object_id=item.id),
        "verification_evaluation": _evaluate_requirement_verification(session, item),
        "history": list_requirement_history(session, item.id),
        "impact": build_impact(session, item.project_id, "requirement", item.id),
    }


def get_component_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, Component, obj_id)
    if item is None:
        raise LookupError("Component not found")
    impacts = [ChangeImpactRead.model_validate(x) for x in _items(session.exec(select(ChangeImpact).where(ChangeImpact.object_type == "component", ChangeImpact.object_id == obj_id)))]
    return {
        "component": ComponentRead.model_validate(item),
        "links": list_links(session, item.project_id, "component", item.id),
        "verification_evidence": list_verification_evidence(session, item.project_id, internal_object_type=FederatedInternalObjectType.component, internal_object_id=item.id),
        "impact": build_impact(session, item.project_id, "component", item.id),
        "change_impacts": impacts,
    }


def get_test_case_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    runs = [TestRunRead.model_validate(x) for x in _items(session.exec(select(TestRun).where(TestRun.test_case_id == obj_id).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))))]
    return {
        "test_case": TestCaseRead.model_validate(item),
        "links": list_links(session, item.project_id, "test_case", item.id),
        "artifact_links": list_artifact_links(session, item.project_id, internal_object_type=FederatedInternalObjectType.test_case, internal_object_id=item.id),
        "verification_evidence": list_verification_evidence(session, item.project_id, internal_object_type=FederatedInternalObjectType.test_case, internal_object_id=item.id),
        "runs": runs,
        "history": list_test_case_history(session, item.id),
        "impact": build_impact(session, item.project_id, "test_case", item.id),
    }


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


def _evaluate_requirement_verification(session: Session, requirement: Requirement) -> RequirementVerificationEvaluation:
    evidence = list_verification_evidence(
        session,
        requirement.project_id,
        internal_object_type=FederatedInternalObjectType.requirement,
        internal_object_id=requirement.id,
    )
    requirement_links = list_links(session, requirement.project_id, "requirement", requirement.id)
    verification_links = [
        link
        for link in requirement_links
        if link.relation_type == RelationType.verifies and link.target_type == LinkObjectType.test_case
    ]
    operational_links = [
        link
        for link in requirement_links
        if link.relation_type == RelationType.reports_on and link.source_type == LinkObjectType.operational_run and link.target_type == LinkObjectType.requirement
    ]
    latest_runs: dict[UUID, TestRun | None] = {link.target_id: _latest_test_run(session, link.target_id) for link in verification_links}
    freshness_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    fresh_evidence_count = 0
    stale_evidence_count = 0
    for item in evidence:
        observed_at = _utc_datetime(item.observed_at)
        if observed_at is None or observed_at < freshness_cutoff:
            stale_evidence_count += 1
        else:
            fresh_evidence_count += 1

    fresh_operational_run_count = 0
    stale_operational_run_count = 0
    successful_operational_run_count = 0
    degraded_operational_run_count = 0
    failed_operational_run_count = 0
    operational_runs = [resolve_object(session, "operational_run", link.source_id)["raw"] for link in operational_links]
    operational_cutoff = date.today() - timedelta(days=30)
    for run in operational_runs:
        if run.date < operational_cutoff:
            stale_operational_run_count += 1
        else:
            fresh_operational_run_count += 1
        if run.outcome == OperationalOutcome.success:
            successful_operational_run_count += 1
        elif run.outcome == OperationalOutcome.degraded:
            degraded_operational_run_count += 1
        elif run.outcome == OperationalOutcome.failure:
            failed_operational_run_count += 1

    linked_test_case_count = len(verification_links)
    passed_test_case_count = 0
    partial_test_case_count = 0
    failed_test_case_count = 0
    missing_test_case_count = 0
    for link in verification_links:
        latest_run = latest_runs.get(link.target_id)
        if latest_run is None:
            missing_test_case_count += 1
        elif latest_run.result == TestRunResult.passed:
            passed_test_case_count += 1
        elif latest_run.result == TestRunResult.partial:
            partial_test_case_count += 1
        elif latest_run.result == TestRunResult.failed:
            failed_test_case_count += 1

    linked_evidence_count = len(evidence)
    linked_operational_run_count = len(operational_runs)
    has_any_verification_input = bool(linked_evidence_count or linked_operational_run_count)

    def _base_kwargs(reasons: list[str], status: RequirementVerificationStatus) -> RequirementVerificationEvaluation:
        return RequirementVerificationEvaluation(
            status=status,
            reasons=reasons,
            linked_evidence_count=linked_evidence_count,
            fresh_evidence_count=fresh_evidence_count,
            stale_evidence_count=stale_evidence_count,
            linked_operational_run_count=linked_operational_run_count,
            fresh_operational_run_count=fresh_operational_run_count,
            stale_operational_run_count=stale_operational_run_count,
            successful_operational_run_count=successful_operational_run_count,
            degraded_operational_run_count=degraded_operational_run_count,
            failed_operational_run_count=failed_operational_run_count,
            linked_test_case_count=linked_test_case_count,
            passed_test_case_count=passed_test_case_count,
            partial_test_case_count=partial_test_case_count,
            failed_test_case_count=failed_test_case_count,
        )

    if not has_any_verification_input:
        return _base_kwargs(["No verification evidence or operational evidence batches are linked."], RequirementVerificationStatus.not_covered)

    if failed_test_case_count > 0 or failed_operational_run_count > 0:
        reasons = []
        if failed_test_case_count > 0:
            reasons.append(f"{failed_test_case_count} linked test case(s) have a failed latest run.")
        if failed_operational_run_count > 0:
            reasons.append(f"{failed_operational_run_count} operational evidence batch(es) recorded a failure.")
        return _base_kwargs(reasons, RequirementVerificationStatus.failed)

    if stale_evidence_count > 0 or stale_operational_run_count > 0 or degraded_operational_run_count > 0:
        reasons = []
        if stale_evidence_count > 0:
            reasons.append(f"{stale_evidence_count} evidence record(s) are stale or missing observed dates.")
        if stale_operational_run_count > 0:
            reasons.append(f"{stale_operational_run_count} operational evidence batch(es) are stale.")
        if degraded_operational_run_count > 0:
            reasons.append(f"{degraded_operational_run_count} operational evidence batch(es) reported degradation.")
        return _base_kwargs(reasons, RequirementVerificationStatus.at_risk)

    if requirement.verification_method == VerificationMethod.test:
        if linked_test_case_count == 0:
            if linked_operational_run_count > 0:
                return _base_kwargs(["Operational evidence batches are linked and current."], RequirementVerificationStatus.verified)
            return _base_kwargs(["Evidence exists, but no linked test case has been attached."], RequirementVerificationStatus.partially_verified)
        if passed_test_case_count == linked_test_case_count:
            reasons = ["Fresh evidence and passing linked tests support verification."]
            if linked_operational_run_count > 0:
                reasons.append("Operational evidence batches also support the requirement.")
            return _base_kwargs(reasons, RequirementVerificationStatus.verified)
        if partial_test_case_count > 0 or missing_test_case_count > 0:
            return _base_kwargs(["Some linked test cases are partial or have not been run yet."], RequirementVerificationStatus.at_risk)
        return _base_kwargs(["Evidence exists, but the linked test set is incomplete."], RequirementVerificationStatus.partially_verified)

    if passed_test_case_count == linked_test_case_count and linked_test_case_count > 0:
        reasons = ["Fresh evidence covers the requirement."]
        if linked_operational_run_count > 0:
            reasons.append("Operational evidence batches are also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified)

    if linked_operational_run_count > 0:
        return _base_kwargs(["Operational evidence batches are linked and current."], RequirementVerificationStatus.verified)

    return _base_kwargs(["Fresh evidence exists, but the verification trail is still incomplete."], RequirementVerificationStatus.partially_verified)


def _verification_evidence_read(
    session: Session,
    evidence: VerificationEvidence,
    linked_objects: list[VerificationEvidenceLink] | None = None,
) -> VerificationEvidenceRead:
    read = VerificationEvidenceRead.model_validate(evidence)
    links = linked_objects if linked_objects is not None else _items(
        session.exec(
            select(VerificationEvidenceLink)
            .where(VerificationEvidenceLink.verification_evidence_id == evidence.id)
            .order_by(VerificationEvidenceLink.created_at, VerificationEvidenceLink.id)
        )
    )
    read.linked_objects = [summarize(resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read


def _validate_verification_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: FederatedInternalObjectType,
    object_id: UUID,
) -> None:
    resolved = resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Verification evidence links must stay within the same project")


def list_verification_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: FederatedInternalObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[VerificationEvidenceRead]:
    evidence_rows = _items(session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project_id).order_by(desc(VerificationEvidence.created_at))))
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(VerificationEvidenceLink)
            .where(VerificationEvidenceLink.verification_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(VerificationEvidenceLink.created_at, VerificationEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[VerificationEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.verification_evidence_id].append(link)
    reads: list[VerificationEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_verification_evidence_read(session, evidence, evidence_links))
    return reads


def create_verification_evidence(session: Session, payload: VerificationEvidenceCreate) -> VerificationEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_test_case_ids = list(dict.fromkeys(payload.linked_test_case_ids))
    linked_component_ids = list(dict.fromkeys(payload.linked_component_ids))
    linked_non_conformity_ids = list(dict.fromkeys(payload.linked_non_conformity_ids))
    if not linked_requirement_ids and not linked_test_case_ids and not linked_component_ids and not linked_non_conformity_ids:
        raise ValueError("Verification evidence must link to at least one requirement, test case, component, or non-conformity")
    for requirement_id in linked_requirement_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.requirement, requirement_id)
    for test_case_id in linked_test_case_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.test_case, test_case_id)
    for component_id in linked_component_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.component, component_id)
    for non_conformity_id in linked_non_conformity_ids:
        _validate_verification_evidence_link(session, payload.project_id, FederatedInternalObjectType.non_conformity, non_conformity_id)
    evidence = VerificationEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_test_case_ids", "linked_component_ids", "linked_non_conformity_ids"}))
    link_rows: list[VerificationEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for test_case_id in linked_test_case_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=test_case_id,
            )
        )
    for component_id in linked_component_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.component,
                internal_object_id=component_id,
            )
        )
    for non_conformity_id in linked_non_conformity_ids:
        link_rows.append(
            VerificationEvidenceLink(
                verification_evidence_id=evidence.id,
                internal_object_type=FederatedInternalObjectType.non_conformity,
                internal_object_id=non_conformity_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _verification_evidence_read(session, evidence, link_rows)


def get_verification_evidence_service(session: Session, evidence_id: UUID) -> VerificationEvidenceRead:
    evidence = _get(session, VerificationEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Verification evidence not found")
    return _verification_evidence_read(session, evidence)


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
        {"project_id": project.id, "key": "DR-CMP-006", "name": "Flight Software", "description": "Autonomy and control software.", "type": ComponentType.software_module, "part_number": "SW-FLT-1", "supplier": "ThreadLite Labs", "status": ComponentStatus.validated, "version": 3, "metadata_json": {"repository": "git@example.com:drone/flight.git", "branch": "main", "entry_point": "src/autonomy/main.py"}},
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

    if tests["DR-TST-001"].status != TestCaseStatus.approved:
        tests["DR-TST-001"].status = TestCaseStatus.approved
        tests["DR-TST-001"].approved_at = datetime.now(timezone.utc)
        tests["DR-TST-001"].approved_by = "seed"
        _touch(tests["DR-TST-001"])
        _add(session, tests["DR-TST-001"])
        _snapshot(session, "test_case", tests["DR-TST-001"], "Approved endurance test for federation seed", "seed")

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
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-006"].id, relation_type=RelationType.allocated_to, rationale="Flight software implements the video pipeline."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-005"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-006"].id, relation_type=RelationType.allocated_to, rationale="Flight software publishes mission telemetry."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-001"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-001"].id, relation_type=RelationType.verifies, rationale="Endurance test verifies endurance."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-002"].id, relation_type=RelationType.verifies, rationale="Streaming test verifies video."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-003"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-003"].id, relation_type=RelationType.verifies, rationale="Temperature test verifies envelope."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-004"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-004"].id, relation_type=RelationType.verifies, rationale="Obstacle test verifies obstacle detection."),
    ]:
        if not session.exec(select(Link).where(Link.project_id == project.id, Link.source_type == p.source_type, Link.source_id == p.source_id, Link.target_type == p.target_type, Link.target_id == p.target_id, Link.relation_type == p.relation_type)).first():
            _add(session, Link.model_validate(p))

    for p in [
        {
            "title": "Endurance verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Seeded endurance evidence tied to the first flight test.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-001",
            "linked_requirement_ids": [reqs["DR-REQ-001"].id],
            "linked_test_case_ids": [tests["DR-TST-001"].id],
        },
        {
            "title": "Streaming verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Seeded streaming evidence tied to the video test.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-002",
            "linked_requirement_ids": [reqs["DR-REQ-002"].id],
            "linked_test_case_ids": [tests["DR-TST-002"].id],
        },
        {
            "title": "Thermal simulation evidence",
            "evidence_type": VerificationEvidenceType.simulation,
            "summary": "Seeded simulation evidence for the temperature envelope requirement.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "Simulink Verification Export",
            "source_reference": "SIM-THERM-001",
            "linked_requirement_ids": [reqs["DR-REQ-003"].id],
            "linked_test_case_ids": [tests["DR-TST-003"].id],
            "metadata_json": {
                "simulation": {
                    "model": "Endurance Model",
                    "scenario": "Thermal envelope validation",
                    "inputs": {"ambient_low_c": -6, "ambient_high_c": 41},
                    "outputs": {"pass": True, "margin_c": 1.0},
                }
            },
        },
        {
            "title": "Obstacle verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Seeded partial obstacle verification evidence.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-004",
            "linked_requirement_ids": [reqs["DR-REQ-004"].id],
            "linked_test_case_ids": [tests["DR-TST-004"].id],
        },
        {
            "title": "Flight software runtime evidence",
            "evidence_type": VerificationEvidenceType.telemetry,
            "summary": "Software module telemetry confirms the flight-control pipeline is active.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "Flight Software",
            "source_reference": "DR-CMP-006",
            "metadata_json": {"software": {"repository": "git@example.com:drone/flight.git", "revision": "a1b2c3d", "runtime": "autonomy"}},
            "linked_requirement_ids": [],
            "linked_test_case_ids": [],
            "linked_component_ids": [comps["DR-CMP-006"].id],
        },
    ]:
        if not session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project.id, VerificationEvidence.title == p["title"])).first():
            create_verification_evidence(
                session,
                VerificationEvidenceCreate(
                    project_id=project.id,
                    title=p["title"],
                    evidence_type=p["evidence_type"],
                    summary=p["summary"],
                    observed_at=p["observed_at"],
                    source_name=p["source_name"],
                    source_reference=p["source_reference"],
                    metadata_json=p.get("metadata_json", {}),
                    linked_requirement_ids=p["linked_requirement_ids"],
                    linked_test_case_ids=p["linked_test_case_ids"],
                    linked_component_ids=p.get("linked_component_ids", []),
                ),
            )

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

    nc = session.exec(select(NonConformity).where(NonConformity.project_id == project.id, NonConformity.key == "NC-001")).first()
    if nc is None:
        nc = _add(session, NonConformity(project_id=project.id, key="NC-001", title="Battery pack overheating during endurance run", description="Observed battery thermal excursion above nominal limits.", status=NonConformityStatus.analyzing, severity=Severity.high))
    if not session.exec(
        select(Link).where(
            Link.project_id == project.id,
            Link.source_type == LinkObjectType.non_conformity,
            Link.source_id == nc.id,
            Link.target_type == LinkObjectType.requirement,
            Link.target_id == reqs["DR-REQ-003"].id,
            Link.relation_type == RelationType.impacts,
        )
    ).first():
        _add(session, Link(project_id=project.id, source_type=LinkObjectType.non_conformity, source_id=nc.id, target_type=LinkObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=RelationType.impacts, rationale="Thermal excursion impacts the environmental requirement."))
    if not session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project.id, VerificationEvidence.title == "Non-conformity thermal observation")).first():
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Non-conformity thermal observation",
                evidence_type=VerificationEvidenceType.inspection,
                summary="Inspection record documenting the overheating issue.",
                observed_at=datetime.now(timezone.utc),
                source_name="Quality Engineering",
                source_reference="NC-001",
                linked_non_conformity_ids=[nc.id],
            ),
        )

    baseline = session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Initial Drone Baseline")).first()
    if baseline is None:
        create_baseline(session, BaselineCreate(project_id=project.id, name="Initial Drone Baseline", description="Baseline for the seeded drone MVP."))

    connectors = {}
    for p in [
        {"name": "DOORS NG", "connector_type": ConnectorType.doors, "base_url": "https://doors.example.local", "description": "Requirement source system."},
        {"name": "Cameo MBSE", "connector_type": ConnectorType.sysml, "base_url": "https://cameo.example.local", "description": "SysML model source."},
        {"name": "Teamcenter PLM", "connector_type": ConnectorType.plm, "base_url": "https://teamcenter.example.local", "description": "Physical part source."},
        {"name": "Simulink Verification Export", "connector_type": ConnectorType.simulation, "base_url": "https://simulink.example.local", "description": "Simulation evidence export."},
    ]:
        connector = session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project.id, ConnectorDefinition.name == p["name"])).first()
        connectors[p["name"]] = connector or _add(session, ConnectorDefinition(project_id=project.id, name=p["name"], connector_type=p["connector_type"], base_url=p["base_url"], description=p["description"], is_active=True, metadata_json={"seeded": True}))

    artifacts = {}
    for p in [
        {"external_id": "REQ-DOORS-001", "artifact_type": ExternalArtifactType.requirement, "name": "Endurance requirement", "description": "Authoritative DOORS requirement for mission endurance.", "connector": "DOORS NG", "canonical_uri": "doors://REQ-DOORS-001", "native_tool_url": "https://doors.example.local/objects/REQ-DOORS-001"},
        {"external_id": "SYSML-BLOCK-BATTERY", "artifact_type": ExternalArtifactType.sysml_element, "name": "Battery Pack", "description": "Authoritative Cameo block for the battery assembly.", "connector": "Cameo MBSE", "canonical_uri": "sysml://SYSML-BLOCK-BATTERY", "native_tool_url": "https://cameo.example.local/elements/SYSML-BLOCK-BATTERY"},
        {"external_id": "PLM-PART-DR-BATT-01", "artifact_type": ExternalArtifactType.cad_part, "name": "Battery Pack Assembly", "description": "Authoritative Teamcenter part for the battery assembly.", "connector": "Teamcenter PLM", "canonical_uri": "plm://PLM-PART-DR-BATT-01", "native_tool_url": "https://teamcenter.example.local/items/PLM-PART-DR-BATT-01"},
        {"external_id": "SIM-FLIGHT-ENDURANCE", "artifact_type": ExternalArtifactType.simulation_model, "name": "Endurance Model", "description": "Simulink model used to validate endurance behavior.", "connector": "Simulink Verification Export", "canonical_uri": "federation://SIM-FLIGHT-ENDURANCE", "native_tool_url": "https://simulink.example.local/models/SIM-FLIGHT-ENDURANCE"},
    ]:
        artifact = session.exec(select(ExternalArtifact).where(ExternalArtifact.project_id == project.id, ExternalArtifact.external_id == p["external_id"])).first()
        artifacts[p["external_id"]] = artifact or _add(
            session,
            ExternalArtifact(
                project_id=project.id,
                connector_definition_id=connectors[p["connector"]].id,
                external_id=p["external_id"],
                artifact_type=p["artifact_type"],
                name=p["name"],
                description=p["description"],
                canonical_uri=p["canonical_uri"],
                native_tool_url=p["native_tool_url"],
                status=ExternalArtifactStatus.active,
                metadata_json={"seeded": True},
            ),
        )

    versions = {}
    for p in [
        {"artifact": "REQ-DOORS-001", "version_label": "7", "revision_label": "7", "metadata_json": {"owner": "systems"}},
        {"artifact": "SYSML-BLOCK-BATTERY", "version_label": "2", "revision_label": "2", "metadata_json": {"model_package": "drone-architecture"}},
        {"artifact": "PLM-PART-DR-BATT-01", "version_label": "C", "revision_label": "C", "metadata_json": {"supplier": "VoltCraft"}},
        {"artifact": "SIM-FLIGHT-ENDURANCE", "version_label": "1.4", "revision_label": "1.4", "metadata_json": {"solver": "Simulink"}},
    ]:
        artifact = artifacts[p["artifact"]]
        version = session.exec(select(ExternalArtifactVersion).where(ExternalArtifactVersion.external_artifact_id == artifact.id, ExternalArtifactVersion.version_label == p["version_label"], ExternalArtifactVersion.revision_label == p["revision_label"])).first()
        versions[f'{p["artifact"]}:{p["version_label"]}'] = version or _add(
            session,
            ExternalArtifactVersion(
                external_artifact_id=artifact.id,
                version_label=p["version_label"],
                revision_label=p["revision_label"],
                checksum_or_signature=f"seed-{p['artifact']}-{p['version_label']}",
                effective_date=date.today(),
                source_timestamp=datetime.now(timezone.utc),
                metadata_json=p["metadata_json"],
            ),
        )

    for p in [
        {"internal_object_type": FederatedInternalObjectType.requirement, "internal_object_id": reqs["DR-REQ-001"].id, "external_artifact_id": artifacts["REQ-DOORS-001"].id, "external_artifact_version_id": versions["REQ-DOORS-001:7"].id, "relation_type": ArtifactLinkRelationType.maps_to, "rationale": "DR-REQ-001 maps to the authoritative DOORS requirement."},
        {"internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "external_artifact_id": artifacts["SYSML-BLOCK-BATTERY"].id, "external_artifact_version_id": versions["SYSML-BLOCK-BATTERY:2"].id, "relation_type": ArtifactLinkRelationType.maps_to, "rationale": "Battery Pack maps to the authoritative Cameo element."},
        {"internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "external_artifact_id": artifacts["PLM-PART-DR-BATT-01"].id, "external_artifact_version_id": versions["PLM-PART-DR-BATT-01:C"].id, "relation_type": ArtifactLinkRelationType.authoritative_reference, "rationale": "Battery Pack is referenced by the Teamcenter part."},
        {"internal_object_type": FederatedInternalObjectType.test_case, "internal_object_id": tests["DR-TST-001"].id, "external_artifact_id": artifacts["SIM-FLIGHT-ENDURANCE"].id, "external_artifact_version_id": versions["SIM-FLIGHT-ENDURANCE:1.4"].id, "relation_type": ArtifactLinkRelationType.validated_against, "rationale": "Endurance test validated against the simulation model."},
    ]:
        if not session.exec(
            select(ArtifactLink).where(
                ArtifactLink.project_id == project.id,
                ArtifactLink.internal_object_type == p["internal_object_type"],
                ArtifactLink.internal_object_id == p["internal_object_id"],
                ArtifactLink.external_artifact_id == p["external_artifact_id"],
                ArtifactLink.relation_type == p["relation_type"],
            )
        ).first():
            _add(
                session,
                ArtifactLink(
                    project_id=project.id,
                    internal_object_type=p["internal_object_type"],
                    internal_object_id=p["internal_object_id"],
                    external_artifact_id=p["external_artifact_id"],
                    external_artifact_version_id=p["external_artifact_version_id"],
                    relation_type=p["relation_type"],
                    rationale=p["rationale"],
                ),
            )

    context = session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project.id, ConfigurationContext.key == "DRN-PDR-0.3")).first()
    if context is None:
        context = _add(
            session,
            ConfigurationContext(
                project_id=project.id,
                key="DRN-PDR-0.3",
                name="Preliminary Design Review 0.3",
                description="Federated configuration snapshot for the seeded drone demo.",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )

    existing_mapping_ids = {
        (mapping.item_kind.value, mapping.internal_object_type.value if mapping.internal_object_type else None, str(mapping.internal_object_id) if mapping.internal_object_id else None, str(mapping.external_artifact_version_id) if mapping.external_artifact_version_id else None)
        for mapping in list_configuration_item_mappings(session, context.id)
    }
    for p in [
        {"item_kind": ConfigurationItemKind.internal_requirement, "internal_object_type": FederatedInternalObjectType.requirement, "internal_object_id": reqs["DR-REQ-001"].id, "internal_object_version": reqs["DR-REQ-001"].version, "role_label": "Approved requirement"},
        {"item_kind": ConfigurationItemKind.internal_block, "internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "internal_object_version": blocks["DR-BLK-004"].version, "role_label": "Approved block"},
        {"item_kind": ConfigurationItemKind.internal_test_case, "internal_object_type": FederatedInternalObjectType.test_case, "internal_object_id": tests["DR-TST-001"].id, "internal_object_version": tests["DR-TST-001"].version, "role_label": "Approved test case"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["REQ-DOORS-001:7"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["SYSML-BLOCK-BATTERY:2"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["PLM-PART-DR-BATT-01:C"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["SIM-FLIGHT-ENDURANCE:1.4"].id, "role_label": "Authoritative external reference"},
    ]:
        key = (
            p["item_kind"].value,
            p.get("internal_object_type").value if p.get("internal_object_type") else None,
            str(p.get("internal_object_id")) if p.get("internal_object_id") else None,
            str(p.get("external_artifact_version_id")) if p.get("external_artifact_version_id") else None,
        )
        if key not in existing_mapping_ids:
            _add(
                session,
                ConfigurationItemMapping(
                    configuration_context_id=context.id,
                    item_kind=p["item_kind"],
                    internal_object_type=p.get("internal_object_type"),
                    internal_object_id=p.get("internal_object_id"),
                    internal_object_version=p.get("internal_object_version"),
                    external_artifact_version_id=p.get("external_artifact_version_id"),
                    role_label=p.get("role_label"),
                    notes=p.get("notes"),
                ),
            )

    return {"project_id": str(project.id), "seeded": True}
