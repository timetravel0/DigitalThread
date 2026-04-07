"""Common service layer for the DigitalThread API."""


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

OBJECT_MODELS = {
    "project": Project,
    "requirement": Requirement,
    "block": Block,
    "component": Component,
    "external_artifact": ExternalArtifact,
    "test_case": TestCase,
    "test_run": TestRun,
    "operational_run": OperationalRun,
    "simulation_evidence": SimulationEvidence,
    "fmi_contract": FMIContract,
    "operational_evidence": OperationalEvidence,
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


def _first_item(result: Any) -> Any | None:
    items = _items(result)
    return items[0] if items else None


_IMPORT_MAX_ROWS = 1000


def _normalize_import_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in row.items():
        if key is None:
            continue
        normalized[key.strip()] = value
    return normalized


def _parse_import_json(content: str) -> list[dict[str, Any]]:
    parsed = json.loads(content)
    if isinstance(parsed, list):
        rows = [_normalize_import_row(item if isinstance(item, dict) else {"value": item}) for item in parsed]
        return [row for row in rows if any(str(value).strip() for value in row.values() if value is not None)]
    if not isinstance(parsed, dict):
        raise ValueError("JSON import content must be an object or array")
    if "records" in parsed and isinstance(parsed["records"], list):
        rows = [_normalize_import_row(item if isinstance(item, dict) else {"value": item}) for item in parsed["records"]]
        return [row for row in rows if any(str(value).strip() for value in row.values() if value is not None)]
    if "items" in parsed and isinstance(parsed["items"], list):
        rows = [_normalize_import_row(item if isinstance(item, dict) else {"value": item}) for item in parsed["items"]]
        return [row for row in rows if any(str(value).strip() for value in row.values() if value is not None)]
    if "external_artifacts" in parsed or "verification_evidence" in parsed:
        rows: list[dict[str, Any]] = []
        for item in parsed.get("external_artifacts", []):
            row = _normalize_import_row(item if isinstance(item, dict) else {"value": item})
            row.setdefault("record_type", "external_artifact")
            if any(str(value).strip() for value in row.values() if value is not None):
                rows.append(row)
        for item in parsed.get("verification_evidence", []):
            row = _normalize_import_row(item if isinstance(item, dict) else {"value": item})
            row.setdefault("record_type", "verification_evidence")
            if any(str(value).strip() for value in row.values() if value is not None):
                rows.append(row)
        return rows
    row = _normalize_import_row(parsed)
    if any(str(value).strip() for value in row.values() if value is not None):
        return [row]
    return []


def _parse_import_csv(content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames or not any(name and name.strip() for name in reader.fieldnames):
        raise ValueError("CSV import content must include a header row")
    rows = [_normalize_import_row(row) for row in reader]
    return [row for row in rows if any(str(value).strip() for value in row.values() if value is not None)]


def _parse_import_rows(format_name: str, content: str) -> list[dict[str, Any]]:
    if format_name == "json":
        rows = _parse_import_json(content)
    elif format_name == "csv":
        rows = _parse_import_csv(content)
    else:
        raise ValueError("Unsupported import format")
    if not rows:
        raise ValueError("Import content did not contain any records")
    if len(rows) > _IMPORT_MAX_ROWS:
        raise ValueError(f"Import contains {len(rows)} records, exceeding the limit of {_IMPORT_MAX_ROWS}")
    return rows


def _parse_import_json_value(value: Any, label: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list, bool, int, float)):
        return value
    text = str(value).strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON") from exc


def _parse_import_datetime(value: Any, label: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return _utc_datetime(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO datetime string") from exc
    return _utc_datetime(parsed)


def _parse_import_uuid(value: Any, label: str) -> UUID | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return UUID(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid UUID") from exc


def _parse_import_uuid_list(value: Any, label: str) -> list[UUID]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        text = str(value).strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = _parse_import_json_value(text, label, default=[])
            if isinstance(parsed, list):
                items = parsed
            else:
                raise ValueError(f"{label} must be a JSON array or semicolon-separated list")
        else:
            items = [item.strip() for item in text.split(";") if item.strip()]
    parsed_ids: list[UUID] = []
    for item in items:
        parsed_ids.append(_parse_import_uuid(item, label) or UUID(int=0))
    return [item for item in parsed_ids if item.int != 0]


def _infer_import_record_type(row: dict[str, Any]) -> str | None:
    record_type = str(row.get("record_type") or row.get("kind") or row.get("type") or "").strip().lower()
    if record_type:
        return record_type
    if "artifact_type" in row or "external_id" in row or "canonical_uri" in row:
        return "external_artifact"
    if "evidence_type" in row or "observed_at" in row or "source_name" in row:
        return "verification_evidence"
    return None


def _status_value(status: Any) -> str:
    return status.value if hasattr(status, "value") else str(status)


def _utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _collect_text_tokens(value: Any) -> list[str]:
    tokens: list[str] = []
    if value is None:
        return tokens
    if isinstance(value, dict):
        for key, item in value.items():
            tokens.extend(_collect_text_tokens(key))
            tokens.extend(_collect_text_tokens(item))
        return tokens
    if isinstance(value, (list, tuple, set)):
        for item in value:
            tokens.extend(_collect_text_tokens(item))
        return tokens
    tokens.append(str(value).strip().lower())
    return tokens


def _verification_signal_from_text(text: str) -> RequirementVerificationStatus | None:
    normalized = " ".join(text.split()).lower()
    fail_terms = ("failed", "failure", "fail", "rejected", "reject", "error", "broken", "false")
    risk_terms = ("at risk", "risk", "warning", "warn", "degraded", "anomaly", "threshold", "unstable", "marginal")
    partial_terms = ("partial", "incomplete", "insufficient", "mixed", "pending")
    verified_terms = ("verified", "pass", "passed", "successful", "success", "supported", "accepted", "true")
    if any(term in normalized for term in fail_terms):
        return RequirementVerificationStatus.failed
    if any(term in normalized for term in risk_terms):
        return RequirementVerificationStatus.at_risk
    if any(term in normalized for term in partial_terms):
        return RequirementVerificationStatus.partially_verified
    if any(term in normalized for term in verified_terms):
        return RequirementVerificationStatus.verified
    return None


def _verification_signal_from_evidence(evidence: VerificationEvidence) -> RequirementVerificationStatus | None:
    tokens: list[str] = []
    tokens.extend(_collect_text_tokens(evidence.title))
    tokens.extend(_collect_text_tokens(evidence.summary))
    tokens.extend(_collect_text_tokens(evidence.source_name))
    tokens.extend(_collect_text_tokens(evidence.source_reference))
    tokens.extend(_collect_text_tokens(evidence.metadata_json))
    combined = " ".join(tokens)
    return _verification_signal_from_text(combined) if combined else None


def _simulation_signal_from_evidence(evidence: SimulationEvidence) -> RequirementVerificationStatus | None:
    if evidence.result == SimulationEvidenceResult.failed:
        return RequirementVerificationStatus.failed
    if evidence.result == SimulationEvidenceResult.partial:
        return RequirementVerificationStatus.partially_verified
    if evidence.result == SimulationEvidenceResult.passed:
        return RequirementVerificationStatus.verified
    return None


def _operational_evidence_signal_from_record(evidence: OperationalEvidence) -> RequirementVerificationStatus | None:
    if evidence.quality_status == OperationalEvidenceQualityStatus.poor:
        return RequirementVerificationStatus.failed
    if evidence.quality_status == OperationalEvidenceQualityStatus.warning:
        return RequirementVerificationStatus.at_risk
    if evidence.quality_status == OperationalEvidenceQualityStatus.good:
        return RequirementVerificationStatus.verified
    return RequirementVerificationStatus.partially_verified


def _threshold_violations(criteria_json: dict[str, Any], measurements: list[tuple[str, dict[str, Any]]]) -> list[str]:
    thresholds = criteria_json.get("telemetry_thresholds") or criteria_json.get("thresholds")
    if not isinstance(thresholds, dict):
        return []
    violations: list[str] = []
    for metric, rule in thresholds.items():
        if not isinstance(rule, dict):
            continue
        min_value = rule.get("min")
        max_value = rule.get("max")
        for source, payload in measurements:
            actual = payload.get(metric)
            if isinstance(actual, (int, float)) and max_value is not None and actual > max_value:
                violations.append(f"{source}: {metric}={actual} exceeds maximum {max_value}.")
            if isinstance(actual, (int, float)) and min_value is not None and actual < min_value:
                violations.append(f"{source}: {metric}={actual} is below minimum {min_value}.")
    return violations


def _verification_status_breakdown(session: Session, requirements: list[Requirement]) -> VerificationStatusBreakdown:
    counts = Counter({status.value: 0 for status in RequirementVerificationStatus})
    for requirement in requirements:
        status = _evaluate_requirement_verification(session, requirement).status.value
        counts[status] += 1
    return VerificationStatusBreakdown(
        verified=counts[RequirementVerificationStatus.verified.value],
        partially_verified=counts[RequirementVerificationStatus.partially_verified.value],
        at_risk=counts[RequirementVerificationStatus.at_risk.value],
        failed=counts[RequirementVerificationStatus.failed.value],
        not_covered=counts[RequirementVerificationStatus.not_covered.value],
    )


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


def _compute_snapshot_hash(
    *,
    project_id: UUID,
    object_type: str,
    object_id: UUID,
    version: int,
    snapshot_json: dict[str, Any],
    previous_snapshot_hash: str | None,
) -> str:
    content_seed = json.dumps(
        {
            "project_id": str(project_id),
            "object_type": object_type,
            "object_id": str(object_id),
            "version": version,
            "snapshot_json": snapshot_json,
            "previous_snapshot_hash": previous_snapshot_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content_seed.encode("utf-8")).hexdigest()


def _snapshot(session: Session, object_type: str, obj: Any, summary: str | None = None, actor: str | None = None) -> None:
    previous_snapshot = _first_item(
        session.exec(
            select(RevisionSnapshot)
            .where(
                RevisionSnapshot.project_id == obj.project_id,
                RevisionSnapshot.object_type == object_type,
                RevisionSnapshot.object_id == obj.id,
            )
            .order_by(desc(RevisionSnapshot.version))
        )
    )
    snapshot_json = obj.model_dump(mode="json")
    previous_snapshot_hash = previous_snapshot.snapshot_hash if previous_snapshot else None
    snapshot_hash = _compute_snapshot_hash(
        project_id=obj.project_id,
        object_type=object_type,
        object_id=obj.id,
        version=getattr(obj, "version", 1),
        snapshot_json=snapshot_json,
        previous_snapshot_hash=previous_snapshot_hash,
    )
    session.add(
        RevisionSnapshot(
            project_id=obj.project_id,
            object_type=object_type,
            object_id=obj.id,
            version=getattr(obj, "version", 1),
            snapshot_json=snapshot_json,
            snapshot_hash=snapshot_hash,
            previous_snapshot_hash=previous_snapshot_hash,
            changed_by=actor,
            change_summary=summary,
        )
    )
    session.commit()


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
    _add(
        session,
        ApprovalActionLog(
            project_id=obj.project_id,
            object_type=object_type,
            object_id=obj.id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            actor=actor,
            comment=comment,
        ),
    )


def _commit(session: Session, obj: Any) -> Any:
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def _editable(status: Any) -> bool:
    return _status_value(status) in {"draft", "rejected"}

def _validate_internal_object(session: Session, object_type: FederatedInternalObjectType, object_id: UUID, project_id: UUID) -> dict[str, Any]:
    resolved = _resolve_object(session, object_type.value, object_id)
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

def _validate_fmi_contract(session: Session, contract_id: UUID, project_id: UUID) -> FMIContract:
    contract = _get(session, FMIContract, contract_id)
    if contract is None:
        raise LookupError("FMI contract not found")
    if contract.project_id != project_id:
        raise ValueError("Referenced FMI contract must stay within the same project")
    return contract

def _ensure_configuration_context_mutable(context: ConfigurationContext) -> None:
    if (
        context.status in {ConfigurationContextStatus.frozen, ConfigurationContextStatus.obsolete}
        or context.context_type == ConfigurationContextType.released
    ):
        raise ValueError("Frozen, released, or obsolete configuration contexts cannot be modified")

def _artifact_read(session: Session, artifact: ExternalArtifact) -> ExternalArtifactRead:
    from app.services.federation_service import list_external_artifact_versions

    read = ExternalArtifactRead.model_validate(artifact)
    connector = _get(session, ConnectorDefinition, artifact.connector_definition_id) if artifact.connector_definition_id else None
    read.connector_name = connector.name if connector else None
    read.connector_type = connector.connector_type if connector else None
    read.versions = list_external_artifact_versions(session, artifact.id)
    return read

def _fmi_contract_read(session: Session, contract: FMIContract) -> FMIContractRead:
    read = FMIContractRead.model_validate(contract)
    read.linked_simulation_evidence_count = len(
        _items(
            session.exec(
                select(SimulationEvidence).where(
                    SimulationEvidence.project_id == contract.project_id,
                    SimulationEvidence.fmi_contract_id == contract.id,
                )
            )
        )
    )
    return read

def _connector_read(session: Session, connector: ConnectorDefinition) -> ConnectorDefinitionRead:
    read = ConnectorDefinitionRead.model_validate(connector)
    read.artifact_count = len(_items(session.exec(select(ExternalArtifact).where(ExternalArtifact.connector_definition_id == connector.id))))
    return read

def _resolve_artifact_link_internal_label(session: Session, link: ArtifactLink) -> str:
    resolved = _resolve_object(session, link.internal_object_type.value, link.internal_object_id)
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

def _resolve_object(session: Session, object_type: str, object_id: UUID) -> dict[str, Any]:
    from app.services.registry_service import resolve_object

    return resolve_object(session, object_type, object_id)

def _seed_profile_demo(
    session: Session,
    *,
    code: str,
    name: str,
    description: str,
    profile: str,
    requirement_key: str,
    requirement_title: str,
    requirement_description: str,
    requirement_category: RequirementCategory,
    requirement_priority: Priority,
    requirement_verification_method: VerificationMethod,
    block_key: str,
    block_name: str,
    block_description: str,
    block_kind: BlockKind,
    block_abstraction_level: AbstractionLevel,
    component_key: str,
    component_name: str,
    component_description: str,
    component_type: ComponentType,
    component_part_number: str | None = None,
    component_supplier: str | None = None,
    component_metadata_json: dict[str, Any] | None = None,
    test_key: str,
    test_title: str,
    test_description: str,
    test_method: TestMethod,
) -> dict[str, Any]:
    from app.services.block_service import create_block, create_block_containment
    from app.services.component_service import create_component
    from app.services.configuration_service import create_configuration_context, create_configuration_item_mapping
    from app.services.evidence_service import create_operational_evidence, create_simulation_evidence, create_verification_evidence
    from app.services.federation_service import create_artifact_link, create_connector, create_external_artifact, create_external_artifact_version
    from app.services.link_service import create_link, create_sysml_relation
    from app.services.requirement_service import create_requirement
    from app.services.test_service import create_test_case
    from app.services.baseline_service import create_baseline, release_baseline
    from app.services.change_request_service import create_change_request

    project = _first_item(session.exec(select(Project).where(Project.code == code)))
    if project is None:
        project = _add(
            session,
            Project(
                code=code,
                name=name,
                description=description,
                domain_profile=profile,
                status=ProjectStatus.active,
            ),
        )
    requirement = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == requirement_key)))
    if requirement is None:
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key=requirement_key,
                title=requirement_title,
                description=requirement_description,
                category=requirement_category,
                priority=requirement_priority,
                verification_method=requirement_verification_method,
                status=RequirementStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        requirement = _get(session, Requirement, requirement.id)
    block = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == block_key)))
    if block is None:
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key=block_key,
                name=block_name,
                description=block_description,
                block_kind=block_kind,
                abstraction_level=block_abstraction_level,
                status=BlockStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        block = _get(session, Block, block.id)
    component = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == component_key)))
    if component is None:
        component = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key=component_key,
                name=component_name,
                description=component_description,
                type=component_type,
                part_number=component_part_number,
                supplier=component_supplier,
                status=ComponentStatus.validated,
                version=1,
                metadata_json=component_metadata_json or {"seeded": True},
            ),
        )
        component = _get(session, Component, component.id)
    test_case = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == test_key)))
    if test_case is None:
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key=test_key,
                title=test_title,
                description=test_description,
                method=test_method,
                status=TestCaseStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        test_case = _get(session, TestCase, test_case.id)
    if requirement is not None and component is not None and not session.exec(
        select(Link).where(
            Link.project_id == project.id,
            Link.source_type == LinkObjectType.requirement,
            Link.source_id == requirement.id,
            Link.target_type == LinkObjectType.component,
            Link.target_id == component.id,
            Link.relation_type == RelationType.allocated_to,
        )
    ).first():
        _add(
            session,
            Link(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.component,
                target_id=component.id,
                relation_type=RelationType.allocated_to,
                rationale=f"{requirement_key} allocates to {component_key}.",
            ),
        )
    if requirement is not None and test_case is not None and not session.exec(
        select(Link).where(
            Link.project_id == project.id,
            Link.source_type == LinkObjectType.requirement,
            Link.source_id == requirement.id,
            Link.target_type == LinkObjectType.test_case,
            Link.target_id == test_case.id,
            Link.relation_type == RelationType.verifies,
        )
    ).first():
        _add(
            session,
            Link(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.test_case,
                target_id=test_case.id,
                relation_type=RelationType.verifies,
                rationale=f"{requirement_key} is verified by {test_key}.",
            ),
        )
    if requirement is not None and block is not None and not session.exec(
        select(SysMLRelation).where(
            SysMLRelation.project_id == project.id,
            SysMLRelation.source_type == SysMLObjectType.block,
            SysMLRelation.source_id == block.id,
            SysMLRelation.target_type == SysMLObjectType.requirement,
            SysMLRelation.target_id == requirement.id,
            SysMLRelation.relation_type == SysMLRelationType.satisfy,
        )
    ).first():
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.block,
                source_id=block.id,
                target_type=SysMLObjectType.requirement,
                target_id=requirement.id,
                relation_type=SysMLRelationType.satisfy,
                rationale=f"{block_key} satisfies {requirement_key}.",
            ),
        )
    if requirement is not None and component is not None and not session.exec(
        select(SysMLRelation).where(
            SysMLRelation.project_id == project.id,
            SysMLRelation.source_type == SysMLObjectType.component,
            SysMLRelation.source_id == component.id,
            SysMLRelation.target_type == SysMLObjectType.requirement,
            SysMLRelation.target_id == requirement.id,
            SysMLRelation.relation_type == SysMLRelationType.trace,
        )
    ).first():
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.component,
                source_id=component.id,
                target_type=SysMLObjectType.requirement,
                target_id=requirement.id,
                relation_type=SysMLRelationType.trace,
                rationale=f"{component_key} realizes {requirement_key}.",
            ),
        )
    if requirement is not None and test_case is not None and not session.exec(
        select(SysMLRelation).where(
            SysMLRelation.project_id == project.id,
            SysMLRelation.source_type == SysMLObjectType.test_case,
            SysMLRelation.source_id == test_case.id,
            SysMLRelation.target_type == SysMLObjectType.requirement,
            SysMLRelation.target_id == requirement.id,
            SysMLRelation.relation_type == SysMLRelationType.verify,
        )
    ).first():
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.test_case,
                source_id=test_case.id,
                target_type=SysMLObjectType.requirement,
                target_id=requirement.id,
                relation_type=SysMLRelationType.verify,
                rationale=f"{test_key} verifies {requirement_key}.",
            ),
        )
    return {
        "project_id": str(project.id),
        "requirement_id": str(requirement.id) if requirement else None,
        "block_id": str(block.id) if block else None,
        "component_id": str(component.id) if component else None,
        "test_case_id": str(test_case.id) if test_case else None,
        "seeded": True,
    }

def _seed_manufacturing_demo_details(session: Session, project_id: UUID, base: dict[str, Any]) -> None:
    from app.services.baseline_service import create_baseline, release_baseline
    from app.services.change_request_service import create_change_request
    from app.services.configuration_service import create_configuration_context, create_configuration_item_mapping
    from app.services.evidence_service import create_operational_evidence, create_simulation_evidence, create_verification_evidence
    from app.services.federation_service import create_artifact_link, create_connector, create_external_artifact, create_external_artifact_version
    from app.services.link_service import create_link, create_sysml_relation
    from app.services.requirement_service import create_requirement
    from app.services.test_service import create_test_case, create_test_run
    from app.services.block_service import create_block, create_block_containment
    from app.services.component_service import create_component

    project = _get(session, Project, project_id)
    if project is None:
        raise LookupError("Project not found")

    req1 = _get(session, Requirement, UUID(base["requirement_id"]))
    blk1 = _get(session, Block, UUID(base["block_id"]))
    comp1 = _get(session, Component, UUID(base["component_id"]))
    tst1 = _get(session, TestCase, UUID(base["test_case_id"]))
    if req1 is None or blk1 is None or comp1 is None or tst1 is None:
        raise LookupError("Manufacturing seed base objects not found")

    req2 = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "MFG-SPEC-002")))
    if req2 is None:
        req2 = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="MFG-SPEC-002",
                title="Line shall reject underfilled units automatically",
                description="Production quality requirement that prevents underfilled packages from leaving the line.",
                category=RequirementCategory.compliance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        req2 = _get(session, Requirement, req2.id)

    blk2 = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == "MFG-BLK-002")))
    if blk2 is None:
        blk2 = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="MFG-BLK-002",
                name="Inspection Station",
                description="Inspection station used to catch underfilled units before release.",
                block_kind=BlockKind.subsystem,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        blk2 = _get(session, Block, blk2.id)

    comp2 = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == "MFG-CMP-002")))
    if comp2 is None:
        comp2 = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="MFG-CMP-002",
                name="Vision Sensor",
                description="Sensor used to detect fill anomalies and route rejects.",
                type=ComponentType.sensor,
                part_number="MFG-VIS-01",
                supplier="Inspecta",
                status=ComponentStatus.validated,
                version=1,
                metadata_json={"resolution_px": 1920, "inspection_mode": "inline"},
            ),
        )
        comp2 = _get(session, Component, comp2.id)

    tst2 = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == "MFG-QC-002")))
    if tst2 is None:
            tst2 = create_test_case(
                session,
                TestCaseCreate(
                    project_id=project.id,
                    key="MFG-QC-002",
                    title="Reject Routing Check",
                    description="Inspection check that underfilled units are routed to the reject lane.",
                    method=TestMethod.inspection,
                    status=TestCaseStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            tst2 = _get(session, TestCase, tst2.id)

    def ensure_requirement(
        key: str,
        title: str,
        description: str,
        category: RequirementCategory,
        priority: Priority,
        verification_method: VerificationMethod,
    ) -> Requirement:
        item = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == key)))
        if item is None:
            item = create_requirement(
                session,
                RequirementCreate(
                    project_id=project.id,
                    key=key,
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    verification_method=verification_method,
                    status=RequirementStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, Requirement, item.id)
        if item is None:
            raise LookupError(f"Manufacturing seed requirement {key} not found")
        return item

    def ensure_block(
        key: str,
        name: str,
        description: str,
        block_kind: BlockKind,
        abstraction_level: AbstractionLevel,
    ) -> Block:
        item = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == key)))
        if item is None:
            item = create_block(
                session,
                BlockCreate(
                    project_id=project.id,
                    key=key,
                    name=name,
                    description=description,
                    block_kind=block_kind,
                    abstraction_level=abstraction_level,
                    status=BlockStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, Block, item.id)
        if item is None:
            raise LookupError(f"Manufacturing seed block {key} not found")
        return item

    def ensure_component(
        key: str,
        name: str,
        description: str,
        component_type: ComponentType,
        *,
        part_number: str | None = None,
        supplier: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Component:
        item = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == key)))
        if item is None:
            item = create_component(
                session,
                ComponentCreate(
                    project_id=project.id,
                    key=key,
                    name=name,
                    description=description,
                    type=component_type,
                    part_number=part_number,
                    supplier=supplier,
                    status=ComponentStatus.validated,
                    version=1,
                    metadata_json=metadata_json or {"seeded": True},
                ),
            )
            item = _get(session, Component, item.id)
        if item is None:
            raise LookupError(f"Manufacturing seed component {key} not found")
        return item

    def ensure_test_case(
        key: str,
        title: str,
        description: str,
        method: TestMethod,
    ) -> TestCase:
        item = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == key)))
        if item is None:
            item = create_test_case(
                session,
                TestCaseCreate(
                    project_id=project.id,
                    key=key,
                    title=title,
                    description=description,
                    method=method,
                    status=TestCaseStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, TestCase, item.id)
        if item is None:
            raise LookupError(f"Manufacturing seed test case {key} not found")
        return item

    req3 = ensure_requirement(
        "MFG-SPEC-003",
        "Caps shall seat before seal at line rate",
        "Caps must be applied cleanly before sealing so the SME can keep the bottle line stable at rated speed.",
        RequirementCategory.performance,
        Priority.high,
        VerificationMethod.test,
    )
    req4 = ensure_requirement(
        "MFG-SPEC-004",
        "Changeover between bottle sizes shall finish within 10 minutes",
        "Small-batch manufacturing needs quick product changeovers to keep the line economical.",
        RequirementCategory.operations,
        Priority.medium,
        VerificationMethod.demonstration,
    )
    req5 = ensure_requirement(
        "MFG-SPEC-005",
        "Operators shall see live batch counters and reject counts",
        "The shift team needs a simple live view of filled units, rejects, and open alerts.",
        RequirementCategory.operations,
        Priority.medium,
        VerificationMethod.inspection,
    )
    req6 = ensure_requirement(
        "MFG-SPEC-006",
        "Reject bin shall alarm before overflow",
        "The reject stream must raise an alarm before the bin reaches a spill condition.",
        RequirementCategory.safety,
        Priority.high,
        VerificationMethod.test,
    )
    req7 = ensure_requirement(
        "MFG-SPEC-007",
        "Guard doors shall stop the line immediately when opened",
        "Operator safety requires immediate stop behavior when line guards are opened.",
        RequirementCategory.safety,
        Priority.critical,
        VerificationMethod.inspection,
    )
    req8 = ensure_requirement(
        "MFG-SPEC-008",
        "Lot and shift identifiers shall be recorded for every batch",
        "The SME needs lightweight traceability from fill run to lot, shift, and operator handover.",
        RequirementCategory.compliance,
        Priority.medium,
        VerificationMethod.analysis,
    )

    blk3 = ensure_block(
        "MFG-BLK-003",
        "Capping Station",
        "Logical and physical capping station that closes the bottle before final seal.",
        BlockKind.subsystem,
        AbstractionLevel.logical,
    )
    blk4 = ensure_block(
        "MFG-BLK-004",
        "Reject Handling Cell",
        "Reject handling cell that routes underfilled or damaged units away from good stock.",
        BlockKind.subsystem,
        AbstractionLevel.logical,
    )
    blk5 = ensure_block(
        "MFG-BLK-005",
        "Controls Cabinet",
        "Controls cabinet hosting the PLC, HMI, and interlock logic used by the SME line.",
        BlockKind.system,
        AbstractionLevel.logical,
    )
    blk6 = ensure_block(
        "MFG-BLK-006",
        "Quality Review Module",
        "Operator review module for batch counts, reject trends, and lot traceability.",
        BlockKind.software,
        AbstractionLevel.logical,
    )

    comp3 = ensure_component(
        "MFG-CMP-003",
        "Servo Capper",
        "Servo-driven capping mechanism used to seat caps consistently before sealing.",
        ComponentType.motor,
        part_number="MFG-CAP-01",
        supplier="PackRight",
        metadata_json={"torque_nm": 1.8, "station": "capping"},
    )
    comp4 = ensure_component(
        "MFG-CMP-004",
        "Reject Gate Actuator",
        "Actuator that diverts non-conforming packs to the reject chute.",
        ComponentType.other,
        part_number="MFG-REJ-01",
        supplier="FlowSort",
        metadata_json={"mode": "divert", "station": "reject-handling"},
    )
    comp5 = ensure_component(
        "MFG-CMP-005",
        "Batch PLC",
        "Controls logic for batch sequencing, interlocks, and line changeover timing.",
        ComponentType.software_module,
        part_number="MFG-PLC-01",
        supplier="LineLogic",
        metadata_json={"firmware": "v3.2", "control_scope": "batch-sequencing"},
    )
    comp6 = ensure_component(
        "MFG-CMP-006",
        "Operator HMI",
        "Simple operator screen for batch counts, reject counters, and line status.",
        ComponentType.software_module,
        part_number="MFG-HMI-01",
        supplier="LineLogic",
        metadata_json={"screen_role": "production-summary"},
    )
    comp7 = ensure_component(
        "MFG-CMP-007",
        "Barcode Scanner",
        "Scanner used to capture lot and shift identifiers for each production batch.",
        ComponentType.sensor,
        part_number="MFG-SCAN-01",
        supplier="TraceFlow",
        metadata_json={"scan_type": "linear", "purpose": "lot-traceability"},
    )

    tst3 = ensure_test_case(
        "MFG-QC-003",
        "Cap Placement Check",
        "Check that caps seat cleanly before the seal station runs at line rate.",
        TestMethod.inspection,
    )
    tst4 = ensure_test_case(
        "MFG-QC-004",
        "Changeover Timing Check",
        "Bench check that the line can switch between bottle sizes inside the 10 minute target.",
        TestMethod.bench,
    )
    tst5 = ensure_test_case(
        "MFG-QC-005",
        "Batch Counter Display Check",
        "Operator check that batch and reject counters are visible on the HMI.",
        TestMethod.inspection,
    )
    tst6 = ensure_test_case(
        "MFG-QC-006",
        "Reject Bin Alarm Check",
        "Quality check that the reject bin raises an alarm before overflow.",
        TestMethod.field,
    )
    tst7 = ensure_test_case(
        "MFG-QC-007",
        "Guard Interlock Check",
        "Safety check that guard door opening stops the line immediately.",
        TestMethod.inspection,
    )
    tst8 = ensure_test_case(
        "MFG-QC-008",
        "Lot Traceability Check",
        "Traceability check that the lot and shift identifier are captured for each batch.",
        TestMethod.inspection,
    )

    for parent_id, child_id in [
        (blk1.id, blk2.id),
        (blk1.id, blk5.id),
        (blk5.id, blk3.id),
        (blk5.id, blk4.id),
        (blk5.id, blk6.id),
    ]:
        if not session.exec(
            select(BlockContainment).where(
                BlockContainment.project_id == project.id,
                BlockContainment.parent_block_id == parent_id,
                BlockContainment.child_block_id == child_id,
            )
        ).first():
            create_block_containment(
                session,
                BlockContainmentCreate(
                    project_id=project.id,
                    parent_block_id=parent_id,
                    child_block_id=child_id,
                    relation_type=BlockContainmentRelationType.contains,
                ),
            )

    manufacturing_relations = [
        (blk3, req3, SysMLRelationType.satisfy, "The capping station satisfies the cap-placement requirement."),
        (blk4, req6, SysMLRelationType.satisfy, "The reject cell satisfies the reject-bin alarm requirement."),
        (blk5, req4, SysMLRelationType.satisfy, "The controls cabinet satisfies the changeover timing requirement."),
        (blk5, req5, SysMLRelationType.satisfy, "The controls cabinet satisfies the live batch visibility requirement."),
        (blk5, req7, SysMLRelationType.satisfy, "The controls cabinet satisfies the guard interlock requirement."),
        (blk6, req8, SysMLRelationType.satisfy, "The quality review module satisfies the lot traceability requirement."),
        (comp3, req3, SysMLRelationType.trace, "The servo capper realizes cap placement."),
        (comp4, req6, SysMLRelationType.trace, "The reject gate actuator realizes reject diversion."),
        (comp5, req4, SysMLRelationType.trace, "The batch PLC realizes rapid changeover."),
        (comp5, req7, SysMLRelationType.trace, "The batch PLC realizes guard interlocks."),
        (comp6, req5, SysMLRelationType.trace, "The operator HMI realizes live batch visibility."),
        (comp7, req8, SysMLRelationType.trace, "The barcode scanner realizes lot traceability."),
        (tst3, req3, SysMLRelationType.verify, "The cap placement check verifies the capping requirement."),
        (tst4, req4, SysMLRelationType.verify, "The changeover timing check verifies the changeover requirement."),
        (tst5, req5, SysMLRelationType.verify, "The batch counter display check verifies the operator visibility requirement."),
        (tst6, req6, SysMLRelationType.verify, "The reject bin alarm check verifies the reject alarm requirement."),
        (tst7, req7, SysMLRelationType.verify, "The guard interlock check verifies the safety stop requirement."),
        (tst8, req8, SysMLRelationType.verify, "The lot traceability check verifies the traceability requirement."),
    ]
    for source, target, relation_type, rationale in manufacturing_relations:
        if not session.exec(
            select(SysMLRelation).where(
                SysMLRelation.project_id == project.id,
                SysMLRelation.source_type == (
                    SysMLObjectType.block
                    if isinstance(source, Block)
                    else SysMLObjectType.component
                    if isinstance(source, Component)
                    else SysMLObjectType.test_case
                ),
                SysMLRelation.source_id == source.id,
                SysMLRelation.target_type == SysMLObjectType.requirement,
                SysMLRelation.target_id == target.id,
                SysMLRelation.relation_type == relation_type,
            )
        ).first():
            create_sysml_relation(
                session,
                SysMLRelationCreate(
                    project_id=project.id,
                    source_type=(
                        SysMLObjectType.block
                        if isinstance(source, Block)
                        else SysMLObjectType.component
                        if isinstance(source, Component)
                        else SysMLObjectType.test_case
                    ),
                    source_id=source.id,
                    target_type=SysMLObjectType.requirement,
                    target_id=target.id,
                    relation_type=relation_type,
                    rationale=rationale,
                ),
            )

    for requirement, component, test_case, rationale in [
        (req3, comp3, tst3, "Cap placement requirement allocates to the servo capper and is verified by the cap check."),
        (req4, comp5, tst4, "Changeover requirement allocates to the batch PLC and is verified by timing."),
        (req5, comp6, tst5, "Batch visibility requirement allocates to the operator HMI and is verified by the display check."),
        (req6, comp4, tst6, "Reject-bin alarm requirement allocates to the reject actuator and is verified by the alarm check."),
        (req7, comp5, tst7, "Guard interlock requirement allocates to the batch PLC and is verified by the interlock check."),
        (req8, comp7, tst8, "Lot traceability requirement allocates to the barcode scanner and is verified by the traceability check."),
    ]:
        for link in [
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.component,
                target_id=component.id,
                relation_type=RelationType.allocated_to,
                rationale=rationale,
            ),
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.test_case,
                target_id=test_case.id,
                relation_type=RelationType.verifies,
                rationale=rationale,
            ),
        ]:
            if not session.exec(
                select(Link).where(
                    Link.project_id == project.id,
                    Link.source_type == link.source_type,
                    Link.source_id == link.source_id,
                    Link.target_type == link.target_type,
                    Link.target_id == link.target_id,
                    Link.relation_type == link.relation_type,
                )
            ).first():
                _add(session, Link.model_validate(link))

    for evidence_payload in [
        {
            "title": "Cap placement verification evidence",
            "summary": "Field evidence shows caps seat cleanly before sealing at line rate.",
            "evidence_type": VerificationEvidenceType.inspection,
            "source_name": "Line QA",
            "source_reference": "MFG-QC-003",
            "linked_requirement_ids": [req3.id],
            "linked_test_case_ids": [tst3.id],
            "linked_component_ids": [comp3.id],
        },
        {
            "title": "Changeover timing verification evidence",
            "summary": "Changeover timing evidence shows the SME line can switch bottle sizes within the 10 minute target.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "Line QA",
            "source_reference": "MFG-QC-004",
            "linked_requirement_ids": [req4.id],
            "linked_test_case_ids": [tst4.id],
            "linked_component_ids": [comp5.id],
        },
        {
            "title": "Batch display verification evidence",
            "summary": "HMI review confirms the batch and reject counters are visible to operators during the shift.",
            "evidence_type": VerificationEvidenceType.analysis,
            "source_name": "Shift Review",
            "source_reference": "MFG-QC-005",
            "linked_requirement_ids": [req5.id],
            "linked_test_case_ids": [tst5.id],
            "linked_component_ids": [comp6.id],
        },
        {
            "title": "Reject bin alarm verification evidence",
            "summary": "Alarm evidence confirms the reject bin notifies the operator before overflow.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "QA Lab",
            "source_reference": "MFG-QC-006",
            "linked_requirement_ids": [req6.id],
            "linked_test_case_ids": [tst6.id],
            "linked_component_ids": [comp4.id],
        },
        {
            "title": "Guard interlock verification evidence",
            "summary": "Safety evidence confirms the guard door stops the line immediately when opened.",
            "evidence_type": VerificationEvidenceType.inspection,
            "source_name": "Safety Audit",
            "source_reference": "MFG-QC-007",
            "linked_requirement_ids": [req7.id],
            "linked_test_case_ids": [tst7.id],
            "linked_component_ids": [comp5.id],
        },
        {
            "title": "Lot traceability verification evidence",
            "summary": "Traceability evidence shows lot and shift identifiers are recorded for every batch.",
            "evidence_type": VerificationEvidenceType.analysis,
            "source_name": "MES Review",
            "source_reference": "MFG-QC-008",
            "linked_requirement_ids": [req8.id],
            "linked_test_case_ids": [tst8.id],
            "linked_component_ids": [comp7.id],
        },
    ]:
        if not session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == evidence_payload["title"],
            )
        ).first():
            create_verification_evidence(
                session,
                VerificationEvidenceCreate(
                    project_id=project.id,
                    title=evidence_payload["title"],
                    evidence_type=evidence_payload["evidence_type"],
                    summary=evidence_payload["summary"],
                    source_name=evidence_payload["source_name"],
                    source_reference=evidence_payload["source_reference"],
                    observed_at=datetime.now(timezone.utc),
                    metadata_json={"seeded": True, "profile": "manufacturing"},
                    linked_requirement_ids=evidence_payload["linked_requirement_ids"],
                    linked_test_case_ids=evidence_payload["linked_test_case_ids"],
                    linked_component_ids=evidence_payload["linked_component_ids"],
                ),
            )

    first_cap_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Cap placement verification evidence",
            )
        )
    )
    first_changeover_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Changeover timing verification evidence",
            )
        )
    )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Manufacturing changeover simulation",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Manufacturing changeover simulation",
                model_reference="Packaging Line Model",
                scenario_name="Bottle size swap with reject burst",
                input_summary="Simulate a short production run that includes a size changeover and a reject burst.",
                inputs_json={"line_speed_units_per_min": 30, "changeover_minutes": 8, "reject_spike_pct": 2.0},
                expected_behavior="The line changes over within the target and rejects are routed without overflow.",
                observed_behavior="Simulation stayed within the changeover target and rejects were routed cleanly.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"seeded": True, "profile": "manufacturing"},
                linked_requirement_ids=[req4.id, req6.id, req7.id],
                linked_test_case_ids=[tst4.id, tst6.id, tst7.id],
                linked_verification_evidence_ids=[e.id for e in [first_cap_evidence, first_changeover_evidence] if e is not None],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Manufacturing quality review telemetry batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Manufacturing quality review telemetry batch",
                source_name="MES aggregator",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(hours=8),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Shift telemetry shows the operator HMI, reject lane, and lot capture stayed aligned through the run.",
                aggregated_observations_json={"batch_counter_visible": True, "reject_lane_clear": True, "lot_capture_complete": True},
                quality_status=OperationalEvidenceQualityStatus.good,
                derived_metrics_json={"counter_visibility_pct": 100, "lot_capture_pct": 100},
                metadata_json={"seeded": True, "profile": "manufacturing"},
                linked_requirement_ids=[req5.id, req6.id, req8.id],
                linked_verification_evidence_ids=[e.id for e in [first_cap_evidence, first_changeover_evidence] if e is not None],
            ),
        )

    if not session.exec(
        select(BlockContainment).where(
            BlockContainment.project_id == project.id,
            BlockContainment.parent_block_id == blk1.id,
            BlockContainment.child_block_id == blk2.id,
        )
    ).first():
        create_block_containment(
            session,
            BlockContainmentCreate(
                project_id=project.id,
                parent_block_id=blk1.id,
                child_block_id=blk2.id,
                relation_type=BlockContainmentRelationType.contains,
            ),
        )

    for rel in [
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blk1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.satisfy, rationale="Packaging line satisfies fill accuracy."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blk2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.satisfy, rationale="Inspection station satisfies reject control."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.component, source_id=comp1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.trace, rationale="Fill head realizes fill accuracy."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.component, source_id=comp2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.trace, rationale="Vision sensor realizes reject control."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tst1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.verify, rationale="Fill accuracy check verifies the fill target."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tst2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.verify, rationale="Reject routing check verifies reject control."),
    ]:
        if not session.exec(
            select(SysMLRelation).where(
                SysMLRelation.project_id == project.id,
                SysMLRelation.source_type == rel.source_type,
                SysMLRelation.source_id == rel.source_id,
                SysMLRelation.target_type == rel.target_type,
                SysMLRelation.target_id == rel.target_id,
                SysMLRelation.relation_type == rel.relation_type,
            )
        ).first():
            create_sysml_relation(session, rel)

    for p in [
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=req2.id, target_type=LinkObjectType.component, target_id=comp2.id, relation_type=RelationType.allocated_to, rationale="Reject control allocates to the vision sensor."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=req2.id, target_type=LinkObjectType.test_case, target_id=tst2.id, relation_type=RelationType.verifies, rationale="Reject routing check verifies the reject control requirement."),
    ]:
        if not session.exec(
            select(Link).where(
                Link.project_id == project.id,
                Link.source_type == p.source_type,
                Link.source_id == p.source_id,
                Link.target_type == p.target_type,
                Link.target_id == p.target_id,
                Link.relation_type == p.relation_type,
            )
        ).first():
            _add(session, Link.model_validate(p))

    for p in [
        {
            "title": "Fill accuracy verification evidence",
            "summary": "Inline quality evidence shows the line stays within the 99.5 percent target.",
            "evidence_type": VerificationEvidenceType.inspection,
            "source_name": "QA Line Audit",
            "source_reference": "MFG-QC-001",
            "linked_requirement_ids": [req1.id],
            "linked_test_case_ids": [tst1.id],
            "linked_component_ids": [comp1.id],
        },
        {
            "title": "Reject routing verification evidence",
            "summary": "Inspection evidence confirms underfilled units are routed to the reject lane.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "QA Lab",
            "source_reference": "MFG-QC-002",
            "linked_requirement_ids": [req2.id],
            "linked_test_case_ids": [tst2.id],
            "linked_component_ids": [comp2.id],
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
                    source_name=p["source_name"],
                    source_reference=p["source_reference"],
                    observed_at=datetime.now(timezone.utc),
                    metadata_json={"seeded": True, "profile": "manufacturing"},
                    linked_requirement_ids=p["linked_requirement_ids"],
                    linked_test_case_ids=p["linked_test_case_ids"],
                    linked_component_ids=p["linked_component_ids"],
                ),
            )

    first_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Fill accuracy verification evidence",
            )
        )
    )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Manufacturing throughput simulation",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Manufacturing throughput simulation",
                model_reference="Production Line Model",
                scenario_name="Peak demand and reject burst",
                input_summary="Simulate a peak shift with short fill variance and intermittent rejects.",
                inputs_json={"shift_units": 2400, "reject_spike_pct": 1.8, "fill_variance_pct": 0.4},
                expected_behavior="Maintain fill accuracy while routing non-conforming units to reject.",
                observed_behavior="Simulation held fill accuracy and routed rejects correctly.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"seeded": True, "profile": "manufacturing"},
                linked_requirement_ids=[req1.id, req2.id],
                linked_test_case_ids=[tst1.id, tst2.id],
                linked_verification_evidence_ids=[first_evidence.id] if first_evidence else [],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Manufacturing shift telemetry batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Manufacturing shift telemetry batch",
                source_name="MES aggregator",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(hours=8),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Shift telemetry shows stable fill accuracy with a controlled reject lane.",
                aggregated_observations_json={"fill_accuracy_pct": 99.6, "reject_rate_pct": 0.3},
                quality_status=OperationalEvidenceQualityStatus.good,
                derived_metrics_json={"fill_accuracy_margin_pct": 0.1, "reject_lane_clear": True},
                metadata_json={"seeded": True, "profile": "manufacturing"},
                linked_requirement_ids=[req1.id, req2.id],
                linked_verification_evidence_ids=[first_evidence.id] if first_evidence else [],
            ),
        )

    baseline = _first_item(session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Manufacturing Release Baseline")))
    if baseline is None:
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Manufacturing Release Baseline",
                description="Released baseline for the packaged line demonstration.",
            ),
        )
    if baseline.status != BaselineStatus.released:
        release_baseline(session, baseline.id)

    cr = _first_item(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project.id, ChangeRequest.key == "MFG-CR-001")))
    if cr is None:
        cr = create_change_request(
            session,
            ChangeRequestCreate(
                project_id=project.id,
                key="MFG-CR-001",
                title="Tune fill-head calibration and line controls after changeover review",
                description="Shift evidence shows the fill head, capper timing, and control logic should be tuned together so the reject lane stays calm and the line keeps its quality cadence.",
                status=ChangeRequestStatus.open,
                severity=Severity.high,
            ),
        )
    if not session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id)).first():
        for impact in [
            {"object_type": "requirement", "object_id": req1.id, "impact_level": ImpactLevel.high, "notes": "Fill accuracy target may need calibration adjustments."},
            {"object_type": "requirement", "object_id": req4.id, "impact_level": ImpactLevel.high, "notes": "Changeover timing depends on line control tuning."},
            {"object_type": "requirement", "object_id": req7.id, "impact_level": ImpactLevel.medium, "notes": "Safety interlocks may need a control review."},
            {"object_type": "component", "object_id": comp1.id, "impact_level": ImpactLevel.high, "notes": "Fill head assembly is the primary tuning lever."},
            {"object_type": "component", "object_id": comp3.id, "impact_level": ImpactLevel.medium, "notes": "Capper timing is part of the coordinated changeover."},
            {"object_type": "component", "object_id": comp5.id, "impact_level": ImpactLevel.high, "notes": "Batch PLC governs the line control change."},
            {"object_type": "test_case", "object_id": tst1.id, "impact_level": ImpactLevel.medium, "notes": "Accuracy check may need tighter acceptance bands."},
            {"object_type": "test_case", "object_id": tst4.id, "impact_level": ImpactLevel.medium, "notes": "Changeover timing should be rechecked after the control update."},
            {"object_type": "test_case", "object_id": tst7.id, "impact_level": ImpactLevel.medium, "notes": "Guard interlock behavior should be revalidated after the control change."},
        ]:
            _add(session, ChangeImpact(change_request_id=cr.id, **impact))

def _seed_personal_demo_details(session: Session, project_id: UUID, base: dict[str, Any]) -> None:
    from app.services.baseline_service import create_baseline, release_baseline
    from app.services.change_request_service import create_change_request
    from app.services.configuration_service import create_configuration_context, create_configuration_item_mapping
    from app.services.evidence_service import create_operational_evidence, create_simulation_evidence, create_verification_evidence
    from app.services.federation_service import create_artifact_link, create_connector, create_external_artifact, create_external_artifact_version
    from app.services.link_service import create_link, create_sysml_relation
    from app.services.requirement_service import create_requirement
    from app.services.test_service import create_test_case, create_test_run
    from app.services.block_service import create_block, create_block_containment
    from app.services.component_service import create_component

    project = _get(session, Project, project_id)
    if project is None:
        raise LookupError("Project not found")

    req1 = _get(session, Requirement, UUID(base["requirement_id"]))
    blk1 = _get(session, Block, UUID(base["block_id"]))
    comp1 = _get(session, Component, UUID(base["component_id"]))
    tst1 = _get(session, TestCase, UUID(base["test_case_id"]))
    if req1 is None or blk1 is None or comp1 is None or tst1 is None:
        raise LookupError("Personal seed base objects not found")

    req2 = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "HOME-GOAL-002")))
    if req2 is None:
        req2 = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="HOME-GOAL-002",
                title="Backups shall restore within 15 minutes",
                description="Personal goal for recovering files quickly after a home outage.",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        req2 = _get(session, Requirement, req2.id)

    blk2 = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == "HOME-BLK-002")))
    if blk2 is None:
        blk2 = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="HOME-BLK-002",
                name="Backup Service",
                description="Home backup workflow that manages snapshots and restore timing.",
                block_kind=BlockKind.subsystem,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
                version=1,
                approved_at=datetime.now(timezone.utc),
                approved_by="seed",
            ),
        )
        blk2 = _get(session, Block, blk2.id)

    comp2 = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == "HOME-CMP-002")))
    if comp2 is None:
        comp2 = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="HOME-CMP-002",
                name="NAS Appliance",
                description="Home storage appliance used to keep backups available overnight.",
                type=ComponentType.other,
                part_number="HOME-NAS-01",
                supplier="SyncedHome",
                status=ComponentStatus.validated,
                version=1,
                metadata_json={"storage_tb": 4, "sync_window": "overnight"},
            ),
        )
        comp2 = _get(session, Component, comp2.id)

    tst2 = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == "HOME-VER-002")))
    if tst2 is None:
            tst2 = create_test_case(
                session,
                TestCaseCreate(
                    project_id=project.id,
                    key="HOME-VER-002",
                    title="Restore Drill",
                    description="Verification drill showing files can be restored inside the 15 minute target.",
                    method=TestMethod.inspection,
                    status=TestCaseStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            tst2 = _get(session, TestCase, tst2.id)

    def ensure_requirement(
        key: str,
        title: str,
        description: str,
        category: RequirementCategory,
        priority: Priority,
        verification_method: VerificationMethod,
    ) -> Requirement:
        item = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == key)))
        if item is None:
            item = create_requirement(
                session,
                RequirementCreate(
                    project_id=project.id,
                    key=key,
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    verification_method=verification_method,
                    status=RequirementStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, Requirement, item.id)
        if item is None:
            raise LookupError(f"Personal seed requirement {key} not found")
        return item

    def ensure_block(
        key: str,
        name: str,
        description: str,
        block_kind: BlockKind,
        abstraction_level: AbstractionLevel,
    ) -> Block:
        item = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == key)))
        if item is None:
            item = create_block(
                session,
                BlockCreate(
                    project_id=project.id,
                    key=key,
                    name=name,
                    description=description,
                    block_kind=block_kind,
                    abstraction_level=abstraction_level,
                    status=BlockStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, Block, item.id)
        if item is None:
            raise LookupError(f"Personal seed block {key} not found")
        return item

    def ensure_component(
        key: str,
        name: str,
        description: str,
        component_type: ComponentType,
        *,
        part_number: str | None = None,
        supplier: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Component:
        item = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == key)))
        if item is None:
            item = create_component(
                session,
                ComponentCreate(
                    project_id=project.id,
                    key=key,
                    name=name,
                    description=description,
                    type=component_type,
                    part_number=part_number,
                    supplier=supplier,
                    status=ComponentStatus.validated,
                    version=1,
                    metadata_json=metadata_json or {"seeded": True},
                ),
            )
            item = _get(session, Component, item.id)
        if item is None:
            raise LookupError(f"Personal seed component {key} not found")
        return item

    def ensure_test_case(
        key: str,
        title: str,
        description: str,
        method: TestMethod,
    ) -> TestCase:
        item = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == key)))
        if item is None:
            item = create_test_case(
                session,
                TestCaseCreate(
                    project_id=project.id,
                    key=key,
                    title=title,
                    description=description,
                    method=method,
                    status=TestCaseStatus.approved,
                    version=1,
                    approved_at=datetime.now(timezone.utc),
                    approved_by="seed",
                ),
            )
            item = _get(session, TestCase, item.id)
        if item is None:
            raise LookupError(f"Personal seed test case {key} not found")
        return item

    req3 = ensure_requirement(
        "HOME-GOAL-003",
        "Guest Wi-Fi shall stay isolated from the backup network",
        "The home network must keep guest devices away from the backup VLAN and storage devices.",
        RequirementCategory.compliance,
        Priority.high,
        VerificationMethod.inspection,
    )
    req4 = ensure_requirement(
        "HOME-GOAL-004",
        "Nightly backup sync shall finish before 02:00",
        "The homelab needs predictable overnight backups that finish before the morning work window.",
        RequirementCategory.performance,
        Priority.medium,
        VerificationMethod.test,
    )
    req5 = ensure_requirement(
        "HOME-GOAL-005",
        "Core networking gear shall ride through a 20 minute outage on UPS",
        "Router, access point, and backup storage should stay up long enough to survive short outages.",
        RequirementCategory.operations,
        Priority.high,
        VerificationMethod.demonstration,
    )
    req6 = ensure_requirement(
        "HOME-GOAL-006",
        "Remote administration shall require VPN access",
        "Remote access should be available only through a VPN gateway instead of direct exposure.",
        RequirementCategory.safety,
        Priority.high,
        VerificationMethod.inspection,
    )
    req7 = ensure_requirement(
        "HOME-GOAL-007",
        "Backup data shall remain encrypted at rest",
        "The home storage platform must keep backup data encrypted when the disks are not in use.",
        RequirementCategory.compliance,
        Priority.medium,
        VerificationMethod.analysis,
    )
    req8 = ensure_requirement(
        "HOME-GOAL-008",
        "A monthly restore drill shall be logged and reviewed",
        "The household should practice a restore so the backup plan stays trustworthy.",
        RequirementCategory.operations,
        Priority.medium,
        VerificationMethod.test,
    )

    blk3 = ensure_block(
        "HOME-BLK-003",
        "Guest Network Segment",
        "Guest Wi-Fi and isolated network segment used for visitors and low-trust devices.",
        BlockKind.subsystem,
        AbstractionLevel.logical,
    )
    blk4 = ensure_block(
        "HOME-BLK-004",
        "Power Resilience Subsystem",
        "Power resilience setup that keeps core services alive during a short outage.",
        BlockKind.subsystem,
        AbstractionLevel.logical,
    )
    blk5 = ensure_block(
        "HOME-BLK-005",
        "Remote Access Gateway",
        "Remote access path used for safe administration of the home lab from outside the house.",
        BlockKind.interface,
        AbstractionLevel.logical,
    )
    blk6 = ensure_block(
        "HOME-BLK-006",
        "Media Sync Service",
        "Nightly synchronization service that keeps media, snapshots, and backup jobs on schedule.",
        BlockKind.software,
        AbstractionLevel.logical,
    )

    comp3 = ensure_component(
        "HOME-CMP-003",
        "Router/Firewall Appliance",
        "Router and firewall used to segment the home network and enforce VPN-only remote access.",
        ComponentType.other,
        part_number="HOME-RTR-01",
        supplier="NetHome",
        metadata_json={"roles": ["routing", "firewall"], "wan_failover": False},
    )
    comp4 = ensure_component(
        "HOME-CMP-004",
        "UPS Unit",
        "Uninterruptible power supply that keeps the core networking gear online during outages.",
        ComponentType.other,
        part_number="HOME-UPS-01",
        supplier="PowerSafe",
        metadata_json={"runtime_minutes": 20, "protected_load": "network-core"},
    )
    comp5 = ensure_component(
        "HOME-CMP-005",
        "VPN Gateway",
        "Software gateway that exposes remote administration only through authenticated VPN access.",
        ComponentType.software_module,
        part_number="HOME-VPN-01",
        supplier="NetHome",
        metadata_json={"protocol": "wireguard", "remote_admin": True},
    )
    comp6 = ensure_component(
        "HOME-CMP-006",
        "Wi-Fi Access Point",
        "Access point for the main home network and guest isolation setup.",
        ComponentType.other,
        part_number="HOME-AP-01",
        supplier="NetHome",
        metadata_json={"ssid_count": 2, "guest_isolation": True},
    )
    comp7 = ensure_component(
        "HOME-CMP-007",
        "Backup Orchestrator",
        "Automation service that schedules backup windows and checks restore drill outcomes.",
        ComponentType.software_module,
        part_number="HOME-BKP-01",
        supplier="SyncedHome",
        metadata_json={"backup_window": "02:00", "drill_cadence": "monthly"},
    )

    tst3 = ensure_test_case(
        "HOME-VER-003",
        "Guest Isolation Check",
        "Check that guest devices cannot reach the backup VLAN or NAS shares.",
        TestMethod.inspection,
    )
    tst4 = ensure_test_case(
        "HOME-VER-004",
        "Backup Window Check",
        "Check that nightly sync completes before the 02:00 window closes.",
        TestMethod.bench,
    )
    tst5 = ensure_test_case(
        "HOME-VER-005",
        "UPS Runtime Check",
        "Check that the core network stays online for at least 20 minutes on UPS.",
        TestMethod.field,
    )
    tst6 = ensure_test_case(
        "HOME-VER-006",
        "Remote Access Check",
        "Check that remote administration requires VPN access and rejects direct exposure.",
        TestMethod.inspection,
    )
    tst7 = ensure_test_case(
        "HOME-VER-007",
        "Encryption-at-Rest Check",
        "Check that backup data remains encrypted when the storage node is offline.",
        TestMethod.inspection,
    )
    tst8 = ensure_test_case(
        "HOME-VER-008",
        "Monthly Drill Review Check",
        "Check that the monthly restore drill is logged and reviewed.",
        TestMethod.inspection,
    )

    for parent_id, child_id in [
        (blk1.id, blk2.id),
        (blk1.id, blk3.id),
        (blk1.id, blk4.id),
        (blk1.id, blk5.id),
        (blk1.id, blk6.id),
    ]:
        if not session.exec(
            select(BlockContainment).where(
                BlockContainment.project_id == project.id,
                BlockContainment.parent_block_id == parent_id,
                BlockContainment.child_block_id == child_id,
            )
        ).first():
            create_block_containment(
                session,
                BlockContainmentCreate(
                    project_id=project.id,
                    parent_block_id=parent_id,
                    child_block_id=child_id,
                    relation_type=BlockContainmentRelationType.contains,
                ),
            )

    personal_relations = [
        (blk3, req3, SysMLRelationType.satisfy, "The guest network segment satisfies guest isolation."),
        (blk4, req5, SysMLRelationType.satisfy, "The power resilience subsystem satisfies outage resilience."),
        (blk5, req6, SysMLRelationType.satisfy, "The remote access gateway satisfies VPN-only administration."),
        (blk6, req4, SysMLRelationType.satisfy, "The media sync service satisfies the overnight sync target."),
        (blk6, req8, SysMLRelationType.satisfy, "The media sync service satisfies the monthly drill cadence."),
        (comp3, req3, SysMLRelationType.trace, "The router/firewall realizes guest isolation."),
        (comp4, req5, SysMLRelationType.trace, "The UPS realizes outage resilience."),
        (comp5, req6, SysMLRelationType.trace, "The VPN gateway realizes remote administration control."),
        (comp6, req3, SysMLRelationType.trace, "The access point realizes guest Wi-Fi segmentation."),
        (comp7, req4, SysMLRelationType.trace, "The backup orchestrator realizes overnight sync timing."),
        (comp7, req8, SysMLRelationType.trace, "The backup orchestrator realizes the monthly drill cadence."),
        (tst3, req3, SysMLRelationType.verify, "The guest isolation check verifies the isolation requirement."),
        (tst4, req4, SysMLRelationType.verify, "The backup window check verifies the overnight sync requirement."),
        (tst5, req5, SysMLRelationType.verify, "The UPS runtime check verifies outage resilience."),
        (tst6, req6, SysMLRelationType.verify, "The remote access check verifies VPN-only administration."),
        (tst7, req7, SysMLRelationType.verify, "The encryption-at-rest check verifies backup encryption."),
        (tst8, req8, SysMLRelationType.verify, "The monthly drill review check verifies the restore drill cadence."),
    ]
    for source, target, relation_type, rationale in personal_relations:
        source_type = (
            SysMLObjectType.block
            if isinstance(source, Block)
            else SysMLObjectType.component
            if isinstance(source, Component)
            else SysMLObjectType.test_case
        )
        if not session.exec(
            select(SysMLRelation).where(
                SysMLRelation.project_id == project.id,
                SysMLRelation.source_type == source_type,
                SysMLRelation.source_id == source.id,
                SysMLRelation.target_type == SysMLObjectType.requirement,
                SysMLRelation.target_id == target.id,
                SysMLRelation.relation_type == relation_type,
            )
        ).first():
            create_sysml_relation(
                session,
                SysMLRelationCreate(
                    project_id=project.id,
                    source_type=source_type,
                    source_id=source.id,
                    target_type=SysMLObjectType.requirement,
                    target_id=target.id,
                    relation_type=relation_type,
                    rationale=rationale,
                ),
            )

    for requirement, component, test_case, rationale in [
        (req3, comp3, tst3, "Guest isolation requirement allocates to the router/firewall and is verified by the isolation check."),
        (req4, comp7, tst4, "Nightly sync requirement allocates to the backup orchestrator and is verified by the backup window check."),
        (req5, comp4, tst5, "UPS resilience requirement allocates to the UPS and is verified by the runtime check."),
        (req6, comp5, tst6, "VPN-only administration requirement allocates to the VPN gateway and is verified by the remote access check."),
        (req7, comp2, tst7, "Encryption-at-rest requirement allocates to the NAS appliance and is verified by the encryption check."),
        (req8, comp7, tst8, "Monthly drill requirement allocates to the backup orchestrator and is verified by the drill review."),
    ]:
        for link in [
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.component,
                target_id=component.id,
                relation_type=RelationType.allocated_to,
                rationale=rationale,
            ),
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.test_case,
                target_id=test_case.id,
                relation_type=RelationType.verifies,
                rationale=rationale,
            ),
        ]:
            if not session.exec(
                select(Link).where(
                    Link.project_id == project.id,
                    Link.source_type == link.source_type,
                    Link.source_id == link.source_id,
                    Link.target_type == link.target_type,
                    Link.target_id == link.target_id,
                    Link.relation_type == link.relation_type,
                )
            ).first():
                _add(session, Link.model_validate(link))

    for evidence_payload in [
        {
            "title": "Guest isolation verification evidence",
            "summary": "Home router evidence confirms guest devices cannot reach the backup VLAN.",
            "evidence_type": VerificationEvidenceType.inspection,
            "source_name": "Home review",
            "source_reference": "HOME-VER-003",
            "linked_requirement_ids": [req3.id],
            "linked_test_case_ids": [tst3.id],
            "linked_component_ids": [comp3.id, comp6.id],
        },
        {
            "title": "Backup window verification evidence",
            "summary": "Backup timing evidence shows the nightly sync finishes before 02:00.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "Backup monitor",
            "source_reference": "HOME-VER-004",
            "linked_requirement_ids": [req4.id],
            "linked_test_case_ids": [tst4.id],
            "linked_component_ids": [comp7.id],
        },
        {
            "title": "UPS runtime verification evidence",
            "summary": "Power evidence confirms the core network survives the outage window on UPS.",
            "evidence_type": VerificationEvidenceType.analysis,
            "source_name": "Power audit",
            "source_reference": "HOME-VER-005",
            "linked_requirement_ids": [req5.id],
            "linked_test_case_ids": [tst5.id],
            "linked_component_ids": [comp4.id],
        },
        {
            "title": "VPN access verification evidence",
            "summary": "Access evidence shows remote administration is only available through VPN.",
            "evidence_type": VerificationEvidenceType.inspection,
            "source_name": "Network review",
            "source_reference": "HOME-VER-006",
            "linked_requirement_ids": [req6.id],
            "linked_test_case_ids": [tst6.id],
            "linked_component_ids": [comp5.id],
        },
        {
            "title": "Encryption-at-rest verification evidence",
            "summary": "Storage review confirms backups are encrypted when the NAS is offline.",
            "evidence_type": VerificationEvidenceType.analysis,
            "source_name": "Storage review",
            "source_reference": "HOME-VER-007",
            "linked_requirement_ids": [req7.id],
            "linked_test_case_ids": [tst7.id],
            "linked_component_ids": [comp2.id],
        },
        {
            "title": "Monthly drill verification evidence",
            "summary": "Restore drill records show the monthly review is logged and repeatable.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "Home QA",
            "source_reference": "HOME-VER-008",
            "linked_requirement_ids": [req8.id],
            "linked_test_case_ids": [tst8.id],
            "linked_component_ids": [comp7.id],
        },
    ]:
        if not session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == evidence_payload["title"],
            )
        ).first():
            create_verification_evidence(
                session,
                VerificationEvidenceCreate(
                    project_id=project.id,
                    title=evidence_payload["title"],
                    evidence_type=evidence_payload["evidence_type"],
                    summary=evidence_payload["summary"],
                    source_name=evidence_payload["source_name"],
                    source_reference=evidence_payload["source_reference"],
                    observed_at=datetime.now(timezone.utc),
                    metadata_json={"seeded": True, "profile": "personal"},
                    linked_requirement_ids=evidence_payload["linked_requirement_ids"],
                    linked_test_case_ids=evidence_payload["linked_test_case_ids"],
                    linked_component_ids=evidence_payload["linked_component_ids"],
                ),
            )

    first_guest_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Guest isolation verification evidence",
            )
        )
    )
    first_backup_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Backup window verification evidence",
            )
        )
    )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Home outage recovery simulation",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Home outage recovery simulation",
                model_reference="Home Network Model",
                scenario_name="Guest traffic and power outage",
                input_summary="Simulate a short outage while backups run and guest devices remain active.",
                inputs_json={"outage_minutes": 20, "backup_window_hours": 8, "guest_clients": 4},
                expected_behavior="Guest devices stay isolated while backups complete inside the window.",
                observed_behavior="The network kept guests isolated and the backup job completed in time.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"seeded": True, "profile": "personal"},
                linked_requirement_ids=[req3.id, req4.id, req5.id],
                linked_test_case_ids=[tst3.id, tst4.id, tst5.id],
                linked_verification_evidence_ids=[e.id for e in [first_guest_evidence, first_backup_evidence] if e is not None],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Home network telemetry batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Home network telemetry batch",
                source_name="Home monitor",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(hours=8),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Telemetry shows the guest network stayed isolated and the backup window completed overnight.",
                aggregated_observations_json={"guest_isolated": True, "backup_completed": True, "vpn_only": True},
                quality_status=OperationalEvidenceQualityStatus.good,
                derived_metrics_json={"backup_success_rate": 1.0, "guest_isolation_checks": 1},
                metadata_json={"seeded": True, "profile": "personal"},
                linked_requirement_ids=[req3.id, req4.id, req6.id, req8.id],
                linked_verification_evidence_ids=[e.id for e in [first_guest_evidence, first_backup_evidence] if e is not None],
            ),
        )

    if not session.exec(
        select(BlockContainment).where(
            BlockContainment.project_id == project.id,
            BlockContainment.parent_block_id == blk1.id,
            BlockContainment.child_block_id == blk2.id,
        )
    ).first():
        create_block_containment(
            session,
            BlockContainmentCreate(
                project_id=project.id,
                parent_block_id=blk1.id,
                child_block_id=blk2.id,
                relation_type=BlockContainmentRelationType.contains,
            ),
        )

    for rel in [
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blk1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.satisfy, rationale="Home system satisfies overnight backup."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blk2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.satisfy, rationale="Backup service satisfies restore timing."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.component, source_id=comp1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.trace, rationale="Backup storage node realizes overnight backup."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.component, source_id=comp2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.trace, rationale="NAS appliance realizes restore timing."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tst1.id, target_type=SysMLObjectType.requirement, target_id=req1.id, relation_type=SysMLRelationType.verify, rationale="Overnight backup check verifies overnight availability."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tst2.id, target_type=SysMLObjectType.requirement, target_id=req2.id, relation_type=SysMLRelationType.verify, rationale="Restore drill verifies restore timing."),
    ]:
        if not session.exec(
            select(SysMLRelation).where(
                SysMLRelation.project_id == project.id,
                SysMLRelation.source_type == rel.source_type,
                SysMLRelation.source_id == rel.source_id,
                SysMLRelation.target_type == rel.target_type,
                SysMLRelation.target_id == rel.target_id,
                SysMLRelation.relation_type == rel.relation_type,
            )
        ).first():
            create_sysml_relation(session, rel)

    for p in [
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=req2.id, target_type=LinkObjectType.component, target_id=comp2.id, relation_type=RelationType.allocated_to, rationale="Restore timing allocates to NAS backup storage."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=req2.id, target_type=LinkObjectType.test_case, target_id=tst2.id, relation_type=RelationType.verifies, rationale="Restore drill verifies the restore goal."),
    ]:
        if not session.exec(
            select(Link).where(
                Link.project_id == project.id,
                Link.source_type == p.source_type,
                Link.source_id == p.source_id,
                Link.target_type == p.target_type,
                Link.target_id == p.target_id,
                Link.relation_type == p.relation_type,
            )
        ).first():
            _add(session, Link.model_validate(p))

    for p in [
        {
            "title": "Overnight backup evidence",
            "summary": "Backup evidence shows the home storage node stayed online overnight.",
            "evidence_type": VerificationEvidenceType.test_result,
            "source_name": "Home backup monitor",
            "source_reference": "HOME-VER-001",
            "linked_requirement_ids": [req1.id],
            "linked_test_case_ids": [tst1.id],
            "linked_component_ids": [comp1.id],
        },
        {
            "title": "Restore drill evidence",
            "summary": "Restore evidence confirms a typical file can be recovered inside the target window.",
            "evidence_type": VerificationEvidenceType.analysis,
            "source_name": "Home QA",
            "source_reference": "HOME-VER-002",
            "linked_requirement_ids": [req2.id],
            "linked_test_case_ids": [tst2.id],
            "linked_component_ids": [comp2.id],
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
                    source_name=p["source_name"],
                    source_reference=p["source_reference"],
                    observed_at=datetime.now(timezone.utc),
                    metadata_json={"seeded": True, "profile": "personal"},
                    linked_requirement_ids=p["linked_requirement_ids"],
                    linked_test_case_ids=p["linked_test_case_ids"],
                    linked_component_ids=p["linked_component_ids"],
                ),
            )

    first_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Overnight backup evidence",
            )
        )
    )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Home backup resilience simulation",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Home backup resilience simulation",
                model_reference="Home Backup Model",
                scenario_name="Power outage overnight",
                input_summary="Simulate a power interruption and nightly backup cadence.",
                inputs_json={"outage_minutes": 35, "backup_window_hours": 8},
                expected_behavior="Backup storage remains reachable and resume window stays within target.",
                observed_behavior="Simulation maintained availability and restore timing stayed within target.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"seeded": True, "profile": "personal"},
                linked_requirement_ids=[req1.id, req2.id],
                linked_test_case_ids=[tst1.id, tst2.id],
                linked_verification_evidence_ids=[first_evidence.id] if first_evidence else [],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Home backup telemetry batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Home backup telemetry batch",
                source_name="Home backup monitor",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(hours=8),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Nightly telemetry shows the backup window completed and the router stayed isolated from guest traffic.",
                aggregated_observations_json={"backup_success": True, "restore_minutes": 12, "guest_isolated": True},
                quality_status=OperationalEvidenceQualityStatus.good,
                derived_metrics_json={"backup_window_hours": 8, "restore_margin_minutes": 3},
                metadata_json={"seeded": True, "profile": "personal"},
                linked_requirement_ids=[req1.id, req2.id],
                linked_verification_evidence_ids=[first_evidence.id] if first_evidence else [],
            ),
        )

    baseline = _first_item(session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Home Infrastructure Baseline")))
    if baseline is None:
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Home Infrastructure Baseline",
                description="Released baseline for the home backup and network setup.",
            ),
        )
    if baseline.status != BaselineStatus.released:
        release_baseline(session, baseline.id)

    cr = _first_item(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project.id, ChangeRequest.key == "HOME-CR-001")))
    if cr is None:
        cr = create_change_request(
            session,
            ChangeRequestCreate(
                project_id=project.id,
                key="HOME-CR-001",
                title="Add UPS-backed storage and VPN hardening for overnight resilience",
                description="The richer home thread shows backups, guest isolation, UPS continuity, and remote access controls should be handled together.",
                status=ChangeRequestStatus.open,
                severity=Severity.medium,
            ),
        )
    if not session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id)).first():
        for impact in [
            {"object_type": "requirement", "object_id": req1.id, "impact_level": ImpactLevel.high, "notes": "Backup availability may require tighter resilience controls."},
            {"object_type": "requirement", "object_id": req3.id, "impact_level": ImpactLevel.medium, "notes": "Guest isolation may need network segmentation review."},
            {"object_type": "requirement", "object_id": req5.id, "impact_level": ImpactLevel.high, "notes": "UPS runtime affects the resilience story."},
            {"object_type": "requirement", "object_id": req6.id, "impact_level": ImpactLevel.medium, "notes": "Remote access policy must align with VPN hardening."},
            {"object_type": "component", "object_id": comp1.id, "impact_level": ImpactLevel.high, "notes": "Backup storage node is the primary resilience concern."},
            {"object_type": "component", "object_id": comp3.id, "impact_level": ImpactLevel.medium, "notes": "Router/firewall segmentation may need a configuration update."},
            {"object_type": "component", "object_id": comp4.id, "impact_level": ImpactLevel.high, "notes": "UPS-backed continuity is the main resilience lever."},
            {"object_type": "component", "object_id": comp5.id, "impact_level": ImpactLevel.medium, "notes": "VPN gateway controls remote administration."},
            {"object_type": "test_case", "object_id": tst1.id, "impact_level": ImpactLevel.medium, "notes": "Overnight backup check may need an additional outage step."},
            {"object_type": "test_case", "object_id": tst3.id, "impact_level": ImpactLevel.medium, "notes": "Guest isolation should be rechecked after the network change."},
            {"object_type": "test_case", "object_id": tst5.id, "impact_level": ImpactLevel.medium, "notes": "UPS runtime should be revalidated after the resilience update."},
        ]:
            _add(session, ChangeImpact(change_request_id=cr.id, **impact))

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

def _sysml_mapping_semantics(relation_type: SysMLRelationType) -> str:
    mapping = {
        SysMLRelationType.satisfy: "Requirement satisfied by a block",
        SysMLRelationType.verify: "Requirement verified by a test case",
        SysMLRelationType.deriveReqt: "Derived requirement relationship",
        SysMLRelationType.refine: "Requirement refinement relationship",
        SysMLRelationType.trace: "General trace relationship",
        SysMLRelationType.allocate: "Allocation relationship",
        SysMLRelationType.contain: "Block containment relationship",
    }
    return mapping.get(relation_type, relation_type.value)

def _step_ap242_semantics(relation_type: ArtifactLinkRelationType) -> str:
    mapping = {
        ArtifactLinkRelationType.authoritative_reference: "Authoritative AP242 part reference",
        ArtifactLinkRelationType.derived_from_external: "Derived from authoritative part",
        ArtifactLinkRelationType.synchronized_with: "Synchronized AP242 part record",
        ArtifactLinkRelationType.validated_against: "Validated against AP242 part version",
        ArtifactLinkRelationType.exported_to: "Exported to AP242 target",
        ArtifactLinkRelationType.maps_to: "ThreadLite part maps to AP242 part",
    }
    return mapping.get(relation_type, relation_type.value)

def _related_baselines_for_configuration_context(session: Session, context: ConfigurationContext) -> list[BaselineRead]:
    from app.services.configuration_service import list_configuration_item_mappings

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

def _released_baselines_for_object(session: Session, project_id: UUID, object_type: BaselineObjectType, object_id: UUID) -> list[BaselineRead]:
    rows = _items(
        session.exec(
            select(Baseline)
            .join(BaselineItem, BaselineItem.baseline_id == Baseline.id)
            .where(
                Baseline.project_id == project_id,
                Baseline.status == BaselineStatus.released,
                BaselineItem.object_type == object_type,
                BaselineItem.object_id == object_id,
            )
            .order_by(desc(Baseline.created_at), desc(Baseline.id))
        )
    )
    return [BaselineRead.model_validate(row) for row in rows]

def _ensure_change_request_for_released_baseline(
    session: Session,
    *,
    project_id: UUID,
    object_type: str,
    object_id: UUID,
    object_label: str,
    reason: str,
) -> ChangeRequestRead | None:
    existing = _first_item(
        session.exec(
            select(ChangeRequest)
            .join(ChangeImpact)
            .where(
                ChangeRequest.project_id == project_id,
                ChangeImpact.object_type == object_type,
                ChangeImpact.object_id == object_id,
                ChangeRequest.status.in_([ChangeRequestStatus.open, ChangeRequestStatus.analysis, ChangeRequestStatus.approved]),
            )
            .order_by(desc(ChangeRequest.created_at), desc(ChangeRequest.id))
        )
    )
    if existing is not None:
        return ChangeRequestRead.model_validate(existing)
    key_prefix = f"CR-REL-{object_type[:3].upper()}-{str(object_id)[:8].upper()}"
    cr = _add(
        session,
        ChangeRequest(
            project_id=project_id,
            key=key_prefix,
            title=f"Released baseline change required for {object_label}",
            description=reason,
            status=ChangeRequestStatus.open,
            severity=Severity.high,
        ),
    )
    _add(
        session,
        ChangeImpact(
            change_request_id=cr.id,
            object_type=object_type,
            object_id=object_id,
            impact_level=ImpactLevel.high,
            notes=reason,
        ),
    )
    session.commit()
    session.refresh(cr)
    return ChangeRequestRead.model_validate(cr)

def _decision_history(session: Session, object_type: str, obj_id: UUID, *, newest_first: bool = True) -> list[ApprovalActionLogRead]:
    order = (desc(ApprovalActionLog.created_at), desc(ApprovalActionLog.id)) if newest_first else (ApprovalActionLog.created_at, ApprovalActionLog.id)
    rows = _items(
        session.exec(
            select(ApprovalActionLog)
            .where(ApprovalActionLog.object_type == object_type, ApprovalActionLog.object_id == obj_id)
            .order_by(*order)
        )
    )
    return [ApprovalActionLogRead.model_validate(item) for item in rows]

def _latest_test_run(session: Session, test_case_id: UUID) -> TestRun | None:
    stmt = select(TestRun).where(TestRun.test_case_id == test_case_id).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))
    items = _items(session.exec(stmt))
    return items[0] if items else None

def _evaluate_requirement_verification(session: Session, requirement: Requirement) -> RequirementVerificationEvaluation:
    from app.services.evidence_service import list_operational_evidence, list_simulation_evidence, list_verification_evidence
    from app.services.link_service import list_links

    evidence = list_verification_evidence(
        session,
        requirement.project_id,
        internal_object_type=FederatedInternalObjectType.requirement,
        internal_object_id=requirement.id,
    )
    simulation_evidence = list_simulation_evidence(
        session,
        requirement.project_id,
        internal_object_type=SimulationEvidenceLinkObjectType.requirement,
        internal_object_id=requirement.id,
    )
    operational_evidence = list_operational_evidence(
        session,
        requirement.project_id,
        internal_object_type=OperationalEvidenceLinkObjectType.requirement,
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
    operational_runs = [_resolve_object(session, "operational_run", link.source_id)["raw"] for link in operational_links]
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

    operational_evidence_signals = [_operational_evidence_signal_from_record(item) for item in operational_evidence]
    simulation_signals = [_simulation_signal_from_evidence(item) for item in simulation_evidence]

    measurement_sources: list[tuple[str, dict[str, Any]]] = []
    for run in operational_runs:
        payload = {k: v for k, v in {
            "duration_minutes": run.duration_minutes,
            "max_temperature_c": run.max_temperature_c,
            "battery_consumption_pct": run.battery_consumption_pct,
            "outcome": _status_value(run.outcome),
        }.items() if v is not None}
        payload.update({k: v for k, v in run.telemetry_json.items() if v is not None})
        measurement_sources.append((f"operational run {getattr(run, 'key', 'run')}", payload))
    for batch in operational_evidence:
        payload = {}
        payload.update(batch.aggregated_observations_json)
        payload.update(batch.derived_metrics_json)
        payload.update({k: v for k, v in batch.metadata_json.items() if v is not None})
        measurement_sources.append((f"operational evidence {batch.title}", payload))
    for simulation in simulation_evidence:
        payload = {}
        payload.update(simulation.inputs_json)
        payload.update({k: v for k, v in simulation.metadata_json.items() if v is not None})
        payload["result"] = simulation.result.value
        measurement_sources.append((f"simulation evidence {simulation.title}", payload))

    threshold_violations = _threshold_violations(getattr(requirement, "verification_criteria_json", {}) or {}, measurement_sources)

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
    linked_operational_evidence_count = len(operational_evidence)
    linked_simulation_evidence_count = len(simulation_evidence)
    has_any_verification_input = bool(
        linked_evidence_count
        or linked_operational_run_count
        or linked_operational_evidence_count
        or linked_simulation_evidence_count
        or linked_test_case_count
    )

    evidence_signals = [_verification_signal_from_evidence(item) for item in evidence]
    explicit_failed_evidence_count = sum(1 for signal in evidence_signals if signal == RequirementVerificationStatus.failed)
    explicit_risk_evidence_count = sum(1 for signal in evidence_signals if signal == RequirementVerificationStatus.at_risk)
    explicit_partial_evidence_count = sum(1 for signal in evidence_signals if signal == RequirementVerificationStatus.partially_verified)
    explicit_verified_evidence_count = sum(1 for signal in evidence_signals if signal == RequirementVerificationStatus.verified)
    explicit_failed_operational_evidence_count = sum(1 for signal in operational_evidence_signals if signal == RequirementVerificationStatus.failed)
    explicit_risk_operational_evidence_count = sum(1 for signal in operational_evidence_signals if signal == RequirementVerificationStatus.at_risk)
    explicit_partial_operational_evidence_count = sum(1 for signal in operational_evidence_signals if signal == RequirementVerificationStatus.partially_verified)
    explicit_verified_operational_evidence_count = sum(1 for signal in operational_evidence_signals if signal == RequirementVerificationStatus.verified)
    explicit_failed_simulation_evidence_count = sum(1 for signal in simulation_signals if signal == RequirementVerificationStatus.failed)
    explicit_risk_simulation_evidence_count = sum(1 for signal in simulation_signals if signal == RequirementVerificationStatus.at_risk)
    explicit_partial_simulation_evidence_count = sum(1 for signal in simulation_signals if signal == RequirementVerificationStatus.partially_verified)
    explicit_verified_simulation_evidence_count = sum(1 for signal in simulation_signals if signal == RequirementVerificationStatus.verified)

    def _base_kwargs(
        reasons: list[str],
        status: RequirementVerificationStatus,
        decision_source: str,
        decision_summary: str | None = None,
    ) -> RequirementVerificationEvaluation:
        return RequirementVerificationEvaluation(
            status=status,
            decision_source=decision_source,
            decision_summary=decision_summary or (reasons[0] if reasons else ""),
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
        return _base_kwargs(
            ["No verification evidence, operational evidence, or linked test cases are present."],
            RequirementVerificationStatus.not_covered,
            "no verification evidence",
        )

    if threshold_violations:
        reasons = ["One or more requirement thresholds were exceeded by telemetry or evidence data."]
        reasons.extend(threshold_violations[:4])
        return _base_kwargs(reasons, RequirementVerificationStatus.failed, "requirement thresholds")

    if explicit_failed_simulation_evidence_count > 0:
        reasons = [f"{explicit_failed_simulation_evidence_count} linked simulation evidence record(s) explicitly indicate failure."]
        if explicit_failed_operational_evidence_count > 0:
            reasons.append(f"{explicit_failed_operational_evidence_count} operational evidence batch(es) explicitly indicate failure.")
        if failed_test_case_count > 0:
            reasons.append(f"{failed_test_case_count} linked test case(s) have a failed latest run.")
        return _base_kwargs(reasons, RequirementVerificationStatus.failed, "simulation evidence")

    if explicit_failed_operational_evidence_count > 0:
        reasons = [f"{explicit_failed_operational_evidence_count} operational evidence batch(es) explicitly indicate failure."]
        if failed_operational_run_count > 0:
            reasons.append(f"{failed_operational_run_count} operational run(s) recorded a failure.")
        return _base_kwargs(reasons, RequirementVerificationStatus.failed, "operational evidence")

    if explicit_failed_evidence_count > 0:
        reasons = [f"{explicit_failed_evidence_count} linked verification evidence record(s) explicitly indicate failure."]
        if failed_test_case_count > 0:
            reasons.append(f"{failed_test_case_count} linked test case(s) have a failed latest run.")
        if failed_operational_run_count > 0:
            reasons.append(f"{failed_operational_run_count} operational evidence batch(es) recorded a failure.")
        return _base_kwargs(reasons, RequirementVerificationStatus.failed, "verification evidence")

    if explicit_risk_simulation_evidence_count > 0:
        reasons = [f"{explicit_risk_simulation_evidence_count} linked simulation evidence record(s) indicate risk or partial completion."]
        if explicit_risk_operational_evidence_count > 0:
            reasons.append(f"{explicit_risk_operational_evidence_count} operational evidence batch(es) indicate risk.")
        if explicit_partial_simulation_evidence_count > 0:
            reasons.append(f"{explicit_partial_simulation_evidence_count} simulation evidence record(s) are partial.")
        return _base_kwargs(reasons, RequirementVerificationStatus.at_risk, "simulation evidence")

    if explicit_risk_operational_evidence_count > 0:
        reasons = [f"{explicit_risk_operational_evidence_count} operational evidence batch(es) indicate risk."]
        if stale_operational_run_count > 0:
            reasons.append(f"{stale_operational_run_count} operational run(s) are stale.")
        return _base_kwargs(reasons, RequirementVerificationStatus.at_risk, "operational evidence")

    if explicit_risk_evidence_count > 0:
        reasons = [f"{explicit_risk_evidence_count} linked verification evidence record(s) explicitly indicate risk or degradation."]
        if stale_evidence_count > 0:
            reasons.append(f"{stale_evidence_count} evidence record(s) are stale or missing observed dates.")
        if stale_operational_run_count > 0:
            reasons.append(f"{stale_operational_run_count} operational evidence batch(es) are stale.")
        if degraded_operational_run_count > 0:
            reasons.append(f"{degraded_operational_run_count} operational evidence batch(es) reported degradation.")
        return _base_kwargs(reasons, RequirementVerificationStatus.at_risk, "verification evidence")

    if explicit_partial_evidence_count > 0:
        reasons = [f"{explicit_partial_evidence_count} linked verification evidence record(s) explicitly indicate incomplete coverage."]
        if linked_test_case_count == 0 and linked_operational_run_count == 0:
            return _base_kwargs(reasons, RequirementVerificationStatus.partially_verified, "verification evidence")
        if requirement.verification_method == VerificationMethod.test and failed_test_case_count == 0 and partial_test_case_count == 0 and missing_test_case_count == 0:
            return _base_kwargs(reasons, RequirementVerificationStatus.partially_verified, "verification evidence")
        return _base_kwargs(reasons, RequirementVerificationStatus.partially_verified, "verification evidence")

    if explicit_verified_evidence_count > 0:
        reasons = ["Linked verification evidence explicitly supports the requirement."]
        if requirement.verification_method == VerificationMethod.test and linked_test_case_count == 0:
            reasons.append("A verification test case is still expected for this requirement.")
            if linked_operational_run_count > 0:
                reasons.append("Operational evidence batches are also current.")
            return _base_kwargs(reasons, RequirementVerificationStatus.partially_verified, "verification evidence")
        if linked_operational_run_count > 0:
            reasons.append("Operational evidence batches are also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified, "verification evidence")

    if explicit_verified_simulation_evidence_count > 0:
        reasons = ["Linked simulation evidence explicitly supports the requirement."]
        if linked_test_case_count == 0 and requirement.verification_method == VerificationMethod.test:
            reasons.append("A verification test case is still expected for this requirement.")
            return _base_kwargs(reasons, RequirementVerificationStatus.partially_verified, "simulation evidence")
        if linked_operational_evidence_count > 0 or linked_operational_run_count > 0:
            reasons.append("Operational feedback is also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified, "simulation evidence")

    if explicit_verified_operational_evidence_count > 0:
        reasons = ["Linked operational evidence explicitly supports the requirement."]
        if linked_operational_run_count > 0:
            reasons.append("Operational runs are also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified, "operational evidence")

    if failed_test_case_count > 0 or failed_operational_run_count > 0:
        reasons = []
        if failed_test_case_count > 0:
            reasons.append(f"{failed_test_case_count} linked test case(s) have a failed latest run.")
        if failed_operational_run_count > 0:
            reasons.append(f"{failed_operational_run_count} operational evidence batch(es) recorded a failure.")
        return _base_kwargs(reasons, RequirementVerificationStatus.failed, "test and operational evidence")

    if stale_evidence_count > 0 or stale_operational_run_count > 0 or degraded_operational_run_count > 0 or explicit_partial_operational_evidence_count > 0 or explicit_partial_simulation_evidence_count > 0:
        reasons = []
        if stale_evidence_count > 0:
            reasons.append(f"{stale_evidence_count} evidence record(s) are stale or missing observed dates.")
        if stale_operational_run_count > 0:
            reasons.append(f"{stale_operational_run_count} operational evidence batch(es) are stale.")
        if degraded_operational_run_count > 0:
            reasons.append(f"{degraded_operational_run_count} operational evidence batch(es) reported degradation.")
        if explicit_partial_operational_evidence_count > 0:
            reasons.append(f"{explicit_partial_operational_evidence_count} operational evidence batch(es) indicate partial coverage.")
        if explicit_partial_simulation_evidence_count > 0:
            reasons.append(f"{explicit_partial_simulation_evidence_count} simulation evidence record(s) indicate partial coverage.")
        return _base_kwargs(reasons, RequirementVerificationStatus.at_risk, "freshness and run health")

    if requirement.verification_method == VerificationMethod.test:
        if linked_test_case_count == 0:
            if linked_evidence_count > 0:
                return _base_kwargs(
                    ["Verification evidence exists, but no linked test case has been attached."],
                    RequirementVerificationStatus.partially_verified,
                    "verification evidence",
                )
            if linked_operational_run_count > 0:
                return _base_kwargs(
                    ["Operational evidence batches are linked, but no verification test case is attached."],
                    RequirementVerificationStatus.partially_verified,
                    "operational evidence fallback",
                )
            return _base_kwargs(["No linked test case has been attached."], RequirementVerificationStatus.not_covered, "no linked test case")
        if failed_test_case_count > 0 or failed_operational_run_count > 0:
            reasons = []
            if failed_test_case_count > 0:
                reasons.append(f"{failed_test_case_count} linked test case(s) have a failed latest run.")
            if failed_operational_run_count > 0:
                reasons.append(f"{failed_operational_run_count} operational evidence batch(es) recorded a failure.")
            return _base_kwargs(reasons, RequirementVerificationStatus.failed, "test and operational evidence")
        if partial_test_case_count > 0 or missing_test_case_count > 0:
            return _base_kwargs(["Some linked test cases are partial or have not been run yet."], RequirementVerificationStatus.at_risk, "linked test case fallback")
        if passed_test_case_count == linked_test_case_count and linked_test_case_count > 0:
            reasons = ["Fresh evidence and passing linked tests support verification."]
            if linked_operational_run_count > 0:
                reasons.append("Operational evidence batches also support the requirement.")
            return _base_kwargs(reasons, RequirementVerificationStatus.verified, "linked test and evidence")
        if linked_evidence_count > 0 or linked_operational_run_count > 0:
            return _base_kwargs(["Verification evidence exists, but the test verification trail is incomplete."], RequirementVerificationStatus.partially_verified, "verification evidence")
        return _base_kwargs(["No verification evidence is linked."], RequirementVerificationStatus.not_covered, "no verification evidence")

    if fresh_evidence_count > 0 and linked_evidence_count > 0:
        reasons = ["Fresh verification evidence supports the requirement."]
        if linked_operational_run_count > 0:
            reasons.append("Operational evidence batches are also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified, "verification evidence")

    if passed_test_case_count == linked_test_case_count and linked_test_case_count > 0:
        reasons = ["Fresh evidence covers the requirement."]
        if linked_operational_run_count > 0:
            reasons.append("Operational evidence batches are also current.")
        return _base_kwargs(reasons, RequirementVerificationStatus.verified, "verification evidence")

    if linked_operational_run_count > 0:
        return _base_kwargs(["Operational evidence batches are linked and current."], RequirementVerificationStatus.verified, "operational evidence fallback")

    if linked_evidence_count > 0:
        return _base_kwargs(["Verification evidence exists, but the verification trail is still incomplete."], RequirementVerificationStatus.partially_verified, "verification evidence")

    if linked_test_case_count > 0:
        if passed_test_case_count == linked_test_case_count:
            return _base_kwargs(["Linked test cases all pass."], RequirementVerificationStatus.verified, "linked test cases")
        if failed_test_case_count > 0:
            return _base_kwargs(["Linked test cases include a failed latest run."], RequirementVerificationStatus.failed, "linked test cases")
        if partial_test_case_count > 0 or missing_test_case_count > 0:
            return _base_kwargs(["Linked test cases are partial or missing runs."], RequirementVerificationStatus.at_risk, "linked test cases")

    return _base_kwargs(["Fresh evidence exists, but the verification trail is still incomplete."], RequirementVerificationStatus.partially_verified, "verification evidence")

def _verification_evidence_read(
    session: Session,
    evidence: VerificationEvidence,
    linked_objects: list[VerificationEvidenceLink] | None = None,
) -> VerificationEvidenceRead:
    from app.services.registry_service import resolve_object, summarize

    read = VerificationEvidenceRead.model_validate(evidence)
    links = linked_objects if linked_objects is not None else _items(
        session.exec(
            select(VerificationEvidenceLink)
            .where(VerificationEvidenceLink.verification_evidence_id == evidence.id)
            .order_by(VerificationEvidenceLink.created_at, VerificationEvidenceLink.id)
        )
    )
    read.linked_objects = [summarize(_resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read

def _validate_verification_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: FederatedInternalObjectType,
    object_id: UUID,
) -> None:
    from app.services.registry_service import resolve_object

    resolved = _resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Verification evidence links must stay within the same project")

def _simulation_evidence_read(
    session: Session,
    evidence: SimulationEvidence,
    linked_objects: list[SimulationEvidenceLink] | None = None,
) -> SimulationEvidenceRead:
    from app.services.fmi_service import get_fmi_contract_service
    from app.services.registry_service import resolve_object, summarize

    read = SimulationEvidenceRead.model_validate(evidence)
    if evidence.fmi_contract_id is not None:
        contract = _get(session, FMIContract, evidence.fmi_contract_id)
        if contract is not None:
            read.fmi_contract_id = contract.id
            read.fmi_contract_key = contract.key
            read.fmi_contract_name = contract.name
            read.fmi_contract_model_identifier = contract.model_identifier
            read.fmi_contract_model_version = contract.model_version
            read.fmi_contract_contract_version = contract.contract_version
    links = linked_objects if linked_objects is not None else _items(
        session.exec(
            select(SimulationEvidenceLink)
            .where(SimulationEvidenceLink.simulation_evidence_id == evidence.id)
            .order_by(SimulationEvidenceLink.created_at, SimulationEvidenceLink.id)
        )
    )
    read.linked_objects = [summarize(_resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read

def _validate_simulation_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: SimulationEvidenceLinkObjectType,
    object_id: UUID,
) -> None:
    from app.services.registry_service import resolve_object

    resolved = _resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Simulation evidence links must stay within the same project")

def _operational_evidence_read(
    session: Session,
    evidence: OperationalEvidence,
    linked_objects: list[OperationalEvidenceLink] | None = None,
) -> OperationalEvidenceRead:
    from app.services.registry_service import resolve_object, summarize

    read = OperationalEvidenceRead.model_validate(evidence)
    links = linked_objects if linked_objects is not None else _items(
        session.exec(
            select(OperationalEvidenceLink)
            .where(OperationalEvidenceLink.operational_evidence_id == evidence.id)
            .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
        )
    )
    read.linked_objects = [summarize(_resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read

def _validate_operational_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: OperationalEvidenceLinkObjectType,
    object_id: UUID,
) -> None:
    from app.services.registry_service import resolve_object

    resolved = _resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Operational evidence links must stay within the same project")
