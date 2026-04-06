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
    elif object_type == "simulation_evidence":
        project_id = obj.project_id
        label = obj.title
        code = obj.model_reference
        status = obj.result
        version = None
    elif object_type == "fmi_contract":
        project_id = obj.project_id
        label = obj.name
        code = obj.model_identifier
        status = obj.contract_version
        version = obj.model_version
    elif object_type == "external_artifact":
        project_id = obj.project_id
        label = obj.name
        code = obj.external_id
        status = obj.status
        version = None
    elif object_type == "operational_evidence":
        project_id = obj.project_id
        label = obj.title
        code = obj.source_name
        status = obj.quality_status
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


def export_project_bundle(session: Session, project_id: UUID) -> dict[str, Any]:
    project = get_project_service(session, project_id)
    connectors = list_connectors(session, project_id)
    external_artifacts = list_external_artifacts(session, project_id)
    fmi_contracts = list_fmi_contracts(session, project_id)
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
    simulation_evidence = list_simulation_evidence(session, project_id)
    operational_evidence = list_operational_evidence(session, project_id)
    sysml_mapping_contract = build_sysml_mapping_contract(session, project_id)
    step_ap242_contract = build_step_ap242_contract(session, project_id)
    operational_evidence_links = [
        OperationalEvidenceLinkRead.model_validate(item).model_dump(mode="json")
        for item in _items(
            session.exec(
                select(OperationalEvidenceLink)
                .join(OperationalEvidence)
                .where(OperationalEvidence.project_id == project_id)
                .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
            )
        )
    ]
    simulation_evidence_links = [
        SimulationEvidenceLinkRead.model_validate(item).model_dump(mode="json")
        for item in _items(
            session.exec(
                select(SimulationEvidenceLink)
                .join(SimulationEvidence)
                .where(SimulationEvidence.project_id == project_id)
                .order_by(SimulationEvidenceLink.created_at, SimulationEvidenceLink.id)
            )
        )
    ]
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
        "simulation_evidence": [evidence.model_dump(mode="json") for evidence in simulation_evidence],
        "simulation_evidence_links": simulation_evidence_links,
        "fmi_contracts": [contract.model_dump(mode="json") for contract in fmi_contracts],
        "operational_evidence": [evidence.model_dump(mode="json") for evidence in operational_evidence],
        "operational_evidence_links": operational_evidence_links,
        "sysml_mapping_contract": sysml_mapping_contract.model_dump(mode="json"),
        "step_ap242_contract": step_ap242_contract.model_dump(mode="json"),
        "change_requests": [ChangeRequestRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "change_impacts": [ChangeImpactRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ChangeImpact).join(ChangeRequest).where(ChangeRequest.project_id == project_id)))],
        "approval_action_logs": [ApprovalActionLogRead.model_validate(item).model_dump(mode="json") for item in _items(session.exec(select(ApprovalActionLog).where(ApprovalActionLog.project_id == project_id)))],
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
    item = Project.model_validate(payload)
    if getattr(item, "domain_profile", "engineering") != "custom":
        item.label_overrides = None
    return _read(ProjectRead, _add(session, item))


def update_project(session: Session, project_id: UUID, payload: ProjectUpdate) -> ProjectRead:
    item = _get(session, Project, project_id)
    if item is None:
        raise LookupError("Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    if getattr(item, "domain_profile", "engineering") != "custom":
        item.label_overrides = None
    _touch(item)
    return _read(ProjectRead, _add(session, item))


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
    released_baselines = _released_baselines_for_object(session, item.project_id, BaselineObjectType.requirement, item.id)
    if released_baselines:
        _ensure_change_request_for_released_baseline(
            session,
            project_id=item.project_id,
            object_type="requirement",
            object_id=item.id,
            object_label=f"{item.key} - {item.title}",
            reason=f"Released baseline(s) {', '.join(b.name for b in released_baselines)} include this requirement and a draft version has been created.",
        )
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
        verification_criteria_json=dict(item.verification_criteria_json or {}),
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
    released_baselines = _released_baselines_for_object(session, item.project_id, BaselineObjectType.component, item.id)
    if released_baselines:
        _ensure_change_request_for_released_baseline(
            session,
            project_id=item.project_id,
            object_type="component",
            object_id=item.id,
            object_label=f"{item.key} - {item.name}",
            reason=f"Released baseline(s) {', '.join(b.name for b in released_baselines)} include this component. A change request is required before editing.",
        )
        raise ValueError("Released baseline components cannot be edited in place. A change request has been created.")
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


def build_sysml_mapping_contract(session: Session, project_id: UUID) -> SysMLMappingContractResponse:
    project = get_project_service(session, project_id)
    requirements = list_requirements(session, project_id)
    blocks = list_blocks(session, project_id)
    sysml_relations = _items(
        session.exec(
            select(SysMLRelation)
            .where(SysMLRelation.project_id == project_id)
            .order_by(SysMLRelation.created_at, SysMLRelation.id)
        )
    )
    containments = list_block_containments(session, project_id)

    requirement_rows: dict[UUID, SysMLRequirementMappingRow] = {
        requirement.id: SysMLRequirementMappingRow(requirement=requirement) for requirement in requirements
    }
    block_rows: dict[UUID, SysMLBlockMappingRow] = {
        block.id: SysMLBlockMappingRow(
            block=block,
            abstraction_level=block.abstraction_level,
            profile_label="Logical block" if block.abstraction_level == AbstractionLevel.logical else "Physical block",
        )
        for block in blocks
    }
    relation_rows: list[SysMLMappingRelationRow] = []
    summary_counts = Counter(
        {
            "requirement": len(requirements),
            "block": len(blocks),
            "logical_block": 0,
            "physical_block": 0,
            "satisfy": 0,
            "verify": 0,
            "deriveReqt": 0,
            "contain": 0,
        }
    )
    for block in blocks:
        if block.abstraction_level == AbstractionLevel.logical:
            summary_counts["logical_block"] += 1
        else:
            summary_counts["physical_block"] += 1

    for containment in containments:
        parent = summarize(resolve_object(session, "block", containment.parent_block_id))
        child = summarize(resolve_object(session, "block", containment.child_block_id))
        relation_rows.append(
            SysMLMappingRelationRow(
                relation_type="contain",
                source=parent,
                target=child,
                semantics="Block containment relation",
            )
        )
        summary_counts["contain"] += 1
        parent_row = block_rows.get(containment.parent_block_id)
        if parent_row is not None:
            parent_row.contained_blocks.append(child)
        child_row = block_rows.get(containment.child_block_id)
        if child_row is not None:
            child_row.contained_in.append(parent)

    for relation in sysml_relations:
        source = summarize(resolve_object(session, relation.source_type.value, relation.source_id))
        target = summarize(resolve_object(session, relation.target_type.value, relation.target_id))
        relation_rows.append(
            SysMLMappingRelationRow(
                relation_type=relation.relation_type.value,
                source=source,
                target=target,
                semantics=_sysml_mapping_semantics(relation.relation_type),
            )
        )
        if relation.relation_type == SysMLRelationType.satisfy and relation.source_type == SysMLObjectType.block and relation.target_type == SysMLObjectType.requirement:
            summary_counts["satisfy"] += 1
            requirement_rows[target.object_id].satisfy_blocks.append(source)
            block_rows[source.object_id].satisfies_requirements.append(target)
        elif relation.relation_type == SysMLRelationType.verify and relation.source_type == SysMLObjectType.test_case and relation.target_type == SysMLObjectType.requirement:
            summary_counts["verify"] += 1
            requirement_rows[target.object_id].verify_tests.append(source)
        elif relation.relation_type == SysMLRelationType.deriveReqt and relation.source_type == SysMLObjectType.requirement and relation.target_type == SysMLObjectType.requirement:
            summary_counts["deriveReqt"] += 1
            requirement_rows[source.object_id].derived_requirements.append(target)
            requirement_rows[target.object_id].derived_from.append(source)

    return SysMLMappingContractResponse(
        project=project,
        generated_at=utcnow(),
        summary=SysMLMappingSummary(
            requirement_count=summary_counts["requirement"],
            block_count=summary_counts["block"],
            logical_block_count=summary_counts["logical_block"],
            physical_block_count=summary_counts["physical_block"],
            satisfy_relation_count=summary_counts["satisfy"],
            verify_relation_count=summary_counts["verify"],
            derive_relation_count=summary_counts["deriveReqt"],
            contain_relation_count=summary_counts["contain"],
        ),
        requirements=sorted(requirement_rows.values(), key=lambda row: row.requirement.key),
        blocks=sorted(block_rows.values(), key=lambda row: row.block.key),
        relations=relation_rows,
    )


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


def build_step_ap242_contract(session: Session, project_id: UUID) -> STEPAP242ContractResponse:
    project = get_project_service(session, project_id)
    components = list_components(session, project_id)
    cad_artifacts = list_external_artifacts(session, project_id, artifact_type=ExternalArtifactType.cad_part)
    artifact_links = _items(
        session.exec(
            select(ArtifactLink)
            .where(
                ArtifactLink.project_id == project_id,
                ArtifactLink.internal_object_type == FederatedInternalObjectType.component,
            )
            .order_by(ArtifactLink.created_at, ArtifactLink.id)
        )
    )
    cad_artifact_map = {artifact.id: artifact for artifact in cad_artifacts}
    part_rows: list[STEPAP242PartRow] = []
    relation_rows: list[STEPAP242RelationRow] = []
    identifier_count = 0

    links_by_component: dict[UUID, list[ArtifactLink]] = defaultdict(list)
    for link in artifact_links:
        if link.external_artifact_id in cad_artifact_map:
            links_by_component[link.internal_object_id].append(link)

    for component in components:
        linked_artifacts: list[ExternalArtifactRead] = []
        identifiers: list[STEPAP242IdentifierRow] = []
        if component.part_number:
            identifiers.append(STEPAP242IdentifierRow(kind="part_number", value=component.part_number, source="component"))
        if component.part_number or links_by_component.get(component.id):
            component_artifacts = []
            seen_artifact_ids: set[UUID] = set()
            for link in links_by_component.get(component.id, []):
                artifact = cad_artifact_map.get(link.external_artifact_id)
                if artifact is None or artifact.id in seen_artifact_ids:
                    continue
                seen_artifact_ids.add(artifact.id)
                component_artifacts.append(artifact)
                identifiers.append(STEPAP242IdentifierRow(kind="external_id", value=artifact.external_id, source="external_artifact"))
                if artifact.canonical_uri:
                    identifiers.append(STEPAP242IdentifierRow(kind="canonical_uri", value=artifact.canonical_uri, source="external_artifact"))
                if artifact.native_tool_url:
                    identifiers.append(STEPAP242IdentifierRow(kind="native_tool_url", value=artifact.native_tool_url, source="external_artifact"))
                relation_rows.append(
                    STEPAP242RelationRow(
                        relation_type=link.relation_type.value,
                        component=summarize(resolve_object(session, "component", component.id)),
                        cad_artifact=artifact,
                        semantics=_step_ap242_semantics(link.relation_type),
                    )
                )
            linked_artifacts = component_artifacts
            identifier_count += len(identifiers)
            part_rows.append(
                STEPAP242PartRow(
                    component=ComponentRead.model_validate(component),
                    part_number=component.part_number,
                    version=component.version,
                    status=_status_value(component.status),
                    supplier=component.supplier,
                    identifiers=identifiers,
                    linked_cad_artifacts=linked_artifacts,
                )
            )

    return STEPAP242ContractResponse(
        project=project,
        generated_at=utcnow(),
        summary=STEPAP242Summary(
            physical_component_count=len(part_rows),
            cad_artifact_count=len(cad_artifacts),
            linked_cad_artifact_count=len({artifact.id for row in part_rows for artifact in row.linked_cad_artifacts}),
            identifier_count=identifier_count,
        ),
        parts=sorted(part_rows, key=lambda row: (row.component.key, row.part_number or "")),
        cad_artifacts=sorted(cad_artifacts, key=lambda artifact: artifact.external_id),
        relations=relation_rows,
    )


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
    return _decision_history(session, "change_request", obj_id, newest_first=False)


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


def submit_change_request_for_analysis(session: Session, obj_id: UUID, payload: WorkflowActionPayload | None = None) -> ChangeRequestRead:
    item = _get(session, ChangeRequest, obj_id)
    if item is None:
        raise LookupError("Change request not found")
    if item.status not in {ChangeRequestStatus.open, ChangeRequestStatus.rejected}:
        raise ValueError("Only open or rejected change requests can move to analysis.")
    old = _status_value(item.status)
    item.status = ChangeRequestStatus.analysis
    item.analysis_summary = payload.comment or payload.reason or item.analysis_summary
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
    item.disposition_summary = payload.comment or payload.reason or item.disposition_summary
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
    item.disposition_summary = payload.comment or payload.reason or item.disposition_summary
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
    item.implementation_summary = payload.comment or payload.reason or item.implementation_summary
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
    item.closure_summary = payload.comment or payload.reason or item.closure_summary
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
    verification_breakdown = _verification_status_breakdown(session, requirements)

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
        verification_status_breakdown=verification_breakdown,
        recent_test_runs=test_runs[:5],
        recent_changes=change_requests[:5],
        recent_links=list_links(session, project_id)[:5],
    )


def get_project_tab_stats(session: Session, project_id: UUID) -> ProjectTabStats:
    requirements = _items(session.exec(select(Requirement).where(Requirement.project_id == project_id)))
    blocks = _items(session.exec(select(Block).where(Block.project_id == project_id)))
    tests = _items(session.exec(select(TestCase).where(TestCase.project_id == project_id)))
    baselines = _items(session.exec(select(Baseline).where(Baseline.project_id == project_id)))
    change_requests = _items(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project_id)))
    non_conformities = _items(session.exec(select(NonConformity).where(NonConformity.project_id == project_id)))
    simulation_evidence = _items(session.exec(select(SimulationEvidence).where(SimulationEvidence.project_id == project_id)))
    operational_evidence = _items(session.exec(select(OperationalEvidence).where(OperationalEvidence.project_id == project_id)))
    operational_runs = _items(session.exec(select(OperationalRun).where(OperationalRun.project_id == project_id)))

    return ProjectTabStats(
        requirements=len(requirements),
        blocks=len(blocks),
        tests=len(tests),
        baselines=len(baselines),
        change_requests=len(change_requests),
        non_conformities=len(non_conformities),
        simulation_evidence=len(simulation_evidence),
        operational_evidence=len(operational_evidence),
        operational_runs=len(operational_runs),
    )


def get_global_dashboard(session: Session) -> GlobalDashboard:
    projects = list_projects_service(session)
    all_requirements = _items(session.exec(select(Requirement)))
    all_links = _items(session.exec(select(Link)))
    all_runs = [TestRunRead.model_validate(item) for item in _items(session.exec(select(TestRun).order_by(desc(TestRun.execution_date), desc(TestRun.created_at))))]
    all_changes = [ChangeRequestRead.model_validate(item) for item in _items(session.exec(select(ChangeRequest).order_by(desc(ChangeRequest.created_at))))]
    verification_breakdown = _verification_status_breakdown(session, all_requirements)
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
        verification_status_breakdown=verification_breakdown,
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
    artifact_links = list_artifact_links(session, project_id)
    sysml_relations = list_sysml_relations(session, project_id)
    containments = list_block_containments(session, project_id)
    active_context_internal_ids = _impact_context_internal_ids(session, project_id)

    adjacency: dict[tuple[str, UUID], set[tuple[str, UUID]]] = defaultdict(set)
    resolved_nodes: dict[tuple[str, UUID], dict[str, Any]] = {root_key: root}

    def resolve_or_cache(node_type: str, node_id: UUID) -> dict[str, Any]:
        key = _impact_node_key(node_type, node_id)
        if key not in resolved_nodes:
            try:
                resolved_nodes[key] = resolve_object(session, node_type, node_id)
            except LookupError:
                resolved_nodes[key] = {
                    "project_id": project_id,
                    "object_type": node_type,
                    "object_id": node_id,
                    "label": f"{node_type}:{node_id} (missing)",
                    "code": None,
                    "status": "missing",
                    "version": None,
                    "raw": None,
                }
        return resolved_nodes[key]

    def add_edge(source_type: str, source_id: UUID, target_type: str, target_id: UUID) -> None:
        source_key = _impact_node_key(source_type, source_id)
        target_key = _impact_node_key(target_type, target_id)
        adjacency[source_key].add(target_key)
        adjacency[target_key].add(source_key)

    for link in legacy_links:
        add_edge(link.source_type.value, link.source_id, link.target_type.value, link.target_id)

    for link in artifact_links:
        try:
            add_edge(link.internal_object_type.value, link.internal_object_id, "external_artifact", link.external_artifact_id)
        except (LookupError, ValueError):
            continue

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

    operational_rows = _items(
        session.exec(
            select(OperationalEvidence)
            .where(OperationalEvidence.project_id == project_id)
            .order_by(desc(OperationalEvidence.captured_at), desc(OperationalEvidence.created_at))
        )
    )
    operational_links = (
        _items(
            session.exec(
                select(OperationalEvidenceLink)
                .where(OperationalEvidenceLink.operational_evidence_id.in_([row.id for row in operational_rows]))
                .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
            )
        )
        if operational_rows
        else []
    )
    operational_links_by_evidence: dict[UUID, list[OperationalEvidenceLink]] = defaultdict(list)
    for link in operational_links:
        operational_links_by_evidence[link.operational_evidence_id].append(link)
    for evidence in operational_rows:
        linked_ids = {
            link.internal_object_id
            for link in operational_links_by_evidence.get(evidence.id, [])
            if link.internal_object_id is not None
        }
        if active_context_internal_ids and not linked_ids.intersection(active_context_internal_ids):
            continue
        for link in operational_links_by_evidence.get(evidence.id, []):
            if link.internal_object_id is None:
                continue
            add_edge("operational_evidence", evidence.id, link.internal_object_type.value, link.internal_object_id)

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
        "simulation_evidence": list_simulation_evidence(session, item.project_id, internal_object_type=SimulationEvidenceLinkObjectType.requirement, internal_object_id=item.id),
        "operational_evidence": list_operational_evidence(session, item.project_id, internal_object_type=OperationalEvidenceLinkObjectType.requirement, internal_object_id=item.id),
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
        "simulation_evidence": list_simulation_evidence(session, item.project_id, internal_object_type=SimulationEvidenceLinkObjectType.test_case, internal_object_id=item.id),
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


def import_project_records(session: Session, project_id: UUID, payload: ProjectImportCreate) -> ProjectImportResponse:
    project = _get(session, Project, project_id)
    if project is None:
        raise LookupError("Project not found")

    rows = _parse_import_rows(payload.format.value, payload.content)
    created_external_artifacts: list[ExternalArtifactRead] = []
    created_verification_evidence: list[VerificationEvidenceRead] = []
    warnings: list[str] = []

    for index, row in enumerate(rows, start=1):
        if not row:
            continue
        record_type = _infer_import_record_type(row)
        if record_type is None:
            raise ValueError(f"Import row {index} is missing a record_type")

        if record_type == "external_artifact":
            artifact_type_raw = row.get("artifact_type")
            name = str(row.get("name") or "").strip()
            external_id = str(row.get("external_id") or "").strip()
            if not external_id:
                raise ValueError(f"Import row {index} is missing external_id")
            if not name:
                raise ValueError(f"Import row {index} is missing name")
            if not artifact_type_raw:
                raise ValueError(f"Import row {index} is missing artifact_type")
            connector_definition_id = _parse_import_uuid(row.get("connector_definition_id"), f"Import row {index} connector_definition_id")
            status_raw = str(row.get("status") or ExternalArtifactStatus.active.value).strip()
            metadata_json = _parse_import_json_value(row.get("metadata_json"), f"Import row {index} metadata_json", default={})
            description = row.get("description")
            canonical_uri = row.get("canonical_uri")
            native_tool_url = row.get("native_tool_url")
            created = create_external_artifact(
                session,
                ExternalArtifactCreate(
                    project_id=project_id,
                    connector_definition_id=connector_definition_id,
                    external_id=external_id,
                    artifact_type=ExternalArtifactType(str(artifact_type_raw).strip().lower()),
                    name=name,
                    description=str(description).strip() if description is not None and str(description).strip() else None,
                    canonical_uri=str(canonical_uri).strip() if canonical_uri is not None and str(canonical_uri).strip() else None,
                    native_tool_url=str(native_tool_url).strip() if native_tool_url is not None and str(native_tool_url).strip() else None,
                    status=ExternalArtifactStatus(status_raw.strip().lower()),
                    metadata_json=metadata_json if isinstance(metadata_json, dict) else {},
                ),
            )
            created_external_artifacts.append(created)
            continue

        if record_type == "verification_evidence":
            title = str(row.get("title") or "").strip()
            if not title:
                raise ValueError(f"Import row {index} is missing title")
            evidence_type_raw = row.get("evidence_type")
            if not evidence_type_raw:
                raise ValueError(f"Import row {index} is missing evidence_type")
            linked_requirement_ids = _parse_import_uuid_list(row.get("linked_requirement_ids"), f"Import row {index} linked_requirement_ids")
            linked_test_case_ids = _parse_import_uuid_list(row.get("linked_test_case_ids"), f"Import row {index} linked_test_case_ids")
            linked_component_ids = _parse_import_uuid_list(row.get("linked_component_ids"), f"Import row {index} linked_component_ids")
            linked_non_conformity_ids = _parse_import_uuid_list(row.get("linked_non_conformity_ids"), f"Import row {index} linked_non_conformity_ids")
            if not linked_requirement_ids and not linked_test_case_ids and not linked_component_ids and not linked_non_conformity_ids:
                raise ValueError(f"Import row {index} must link to at least one requirement, test case, component, or non-conformity")
            metadata_json = _parse_import_json_value(row.get("metadata_json"), f"Import row {index} metadata_json", default={})
            observed_at = _parse_import_datetime(row.get("observed_at"), f"Import row {index} observed_at")
            created = create_verification_evidence(
                session,
                VerificationEvidenceCreate(
                    project_id=project_id,
                    title=title,
                    evidence_type=VerificationEvidenceType(str(evidence_type_raw).strip().lower()),
                    summary=str(row.get("summary") or "").strip(),
                    observed_at=observed_at,
                    source_name=str(row.get("source_name")).strip() if row.get("source_name") is not None and str(row.get("source_name")).strip() else None,
                    source_reference=str(row.get("source_reference")).strip() if row.get("source_reference") is not None and str(row.get("source_reference")).strip() else None,
                    metadata_json=metadata_json if isinstance(metadata_json, dict) else {},
                    linked_requirement_ids=linked_requirement_ids,
                    linked_test_case_ids=linked_test_case_ids,
                    linked_component_ids=linked_component_ids,
                    linked_non_conformity_ids=linked_non_conformity_ids,
                ),
            )
            created_verification_evidence.append(created)
            continue

        warnings.append(f"Import row {index} ignored unsupported record_type '{record_type}'")

    return ProjectImportResponse(
        project=_read(ProjectRead, project),
        summary=ProjectImportSummary(
            parsed_records=len(rows),
            created_external_artifacts=len(created_external_artifacts),
            created_verification_evidence=len(created_verification_evidence),
        ),
        external_artifacts=created_external_artifacts,
        verification_evidence=created_verification_evidence,
        warnings=warnings,
    )


def _simulation_evidence_read(
    session: Session,
    evidence: SimulationEvidence,
    linked_objects: list[SimulationEvidenceLink] | None = None,
) -> SimulationEvidenceRead:
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
    read.linked_objects = [summarize(resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read


def _validate_simulation_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: SimulationEvidenceLinkObjectType,
    object_id: UUID,
) -> None:
    resolved = resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Simulation evidence links must stay within the same project")


def list_fmi_contracts(session: Session, project_id: UUID) -> list[FMIContractRead]:
    rows = _items(
        session.exec(
            select(FMIContract)
            .where(FMIContract.project_id == project_id)
            .order_by(desc(FMIContract.created_at), FMIContract.key)
        )
    )
    return [_fmi_contract_read(session, row) for row in rows]


def create_fmi_contract(session: Session, payload: FMIContractCreate) -> FMIContractRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    contract = FMIContract(**payload.model_dump())
    return _fmi_contract_read(session, _add(session, contract))


def get_fmi_contract_service(session: Session, contract_id: UUID) -> FMIContractDetail:
    contract = _get(session, FMIContract, contract_id)
    if contract is None:
        raise LookupError("FMI contract not found")
    evidence_rows = [
        evidence
        for evidence in list_simulation_evidence(session, contract.project_id)
        if evidence.fmi_contract_id == contract.id
    ]
    return FMIContractDetail(
        fmi_contract=_fmi_contract_read(session, contract),
        simulation_evidence=evidence_rows,
    )


def list_simulation_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: SimulationEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[SimulationEvidenceRead]:
    evidence_rows = _items(
        session.exec(
            select(SimulationEvidence)
            .where(SimulationEvidence.project_id == project_id)
            .order_by(desc(SimulationEvidence.execution_timestamp), desc(SimulationEvidence.created_at))
        )
    )
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(SimulationEvidenceLink)
            .where(SimulationEvidenceLink.simulation_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(SimulationEvidenceLink.created_at, SimulationEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[SimulationEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.simulation_evidence_id].append(link)
    reads: list[SimulationEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_simulation_evidence_read(session, evidence, evidence_links))
    return reads


def create_simulation_evidence(session: Session, payload: SimulationEvidenceCreate) -> SimulationEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_test_case_ids = list(dict.fromkeys(payload.linked_test_case_ids))
    linked_verification_evidence_ids = list(dict.fromkeys(payload.linked_verification_evidence_ids))
    if payload.fmi_contract_id is not None:
        _validate_fmi_contract(session, payload.fmi_contract_id, payload.project_id)
    if not linked_requirement_ids and not linked_test_case_ids and not linked_verification_evidence_ids:
        raise ValueError("Simulation evidence must link to at least one requirement, test case, or verification evidence")
    for requirement_id in linked_requirement_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.requirement, requirement_id)
    for test_case_id in linked_test_case_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.test_case, test_case_id)
    for verification_evidence_id in linked_verification_evidence_ids:
        _validate_simulation_evidence_link(session, payload.project_id, SimulationEvidenceLinkObjectType.verification_evidence, verification_evidence_id)
    evidence = SimulationEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_test_case_ids", "linked_verification_evidence_ids"}))
    link_rows: list[SimulationEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for test_case_id in linked_test_case_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.test_case,
                internal_object_id=test_case_id,
            )
        )
    for verification_evidence_id in linked_verification_evidence_ids:
        link_rows.append(
            SimulationEvidenceLink(
                simulation_evidence_id=evidence.id,
                internal_object_type=SimulationEvidenceLinkObjectType.verification_evidence,
                internal_object_id=verification_evidence_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _simulation_evidence_read(session, evidence, link_rows)


def get_simulation_evidence_service(session: Session, evidence_id: UUID) -> SimulationEvidenceRead:
    evidence = _get(session, SimulationEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Simulation evidence not found")
    return _simulation_evidence_read(session, evidence)


def _operational_evidence_read(
    session: Session,
    evidence: OperationalEvidence,
    linked_objects: list[OperationalEvidenceLink] | None = None,
) -> OperationalEvidenceRead:
    read = OperationalEvidenceRead.model_validate(evidence)
    links = linked_objects if linked_objects is not None else _items(
        session.exec(
            select(OperationalEvidenceLink)
            .where(OperationalEvidenceLink.operational_evidence_id == evidence.id)
            .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
        )
    )
    read.linked_objects = [summarize(resolve_object(session, link.internal_object_type.value, link.internal_object_id)) for link in links]
    return read


def _validate_operational_evidence_link(
    session: Session,
    project_id: UUID,
    object_type: OperationalEvidenceLinkObjectType,
    object_id: UUID,
) -> None:
    resolved = resolve_object(session, object_type.value, object_id)
    if resolved["project_id"] != project_id:
        raise ValueError("Operational evidence links must stay within the same project")


def list_operational_evidence(
    session: Session,
    project_id: UUID,
    internal_object_type: OperationalEvidenceLinkObjectType | None = None,
    internal_object_id: UUID | None = None,
) -> list[OperationalEvidenceRead]:
    evidence_rows = _items(
        session.exec(
            select(OperationalEvidence)
            .where(OperationalEvidence.project_id == project_id)
            .order_by(desc(OperationalEvidence.captured_at), desc(OperationalEvidence.created_at))
        )
    )
    if not evidence_rows:
        return []
    links = _items(
        session.exec(
            select(OperationalEvidenceLink)
            .where(OperationalEvidenceLink.operational_evidence_id.in_([row.id for row in evidence_rows]))
            .order_by(OperationalEvidenceLink.created_at, OperationalEvidenceLink.id)
        )
    )
    grouped: dict[UUID, list[OperationalEvidenceLink]] = defaultdict(list)
    for link in links:
        grouped[link.operational_evidence_id].append(link)
    reads: list[OperationalEvidenceRead] = []
    for evidence in evidence_rows:
        evidence_links = grouped.get(evidence.id, [])
        if internal_object_type is not None and internal_object_id is not None:
            if not any(link.internal_object_type == internal_object_type and link.internal_object_id == internal_object_id for link in evidence_links):
                continue
        reads.append(_operational_evidence_read(session, evidence, evidence_links))
    return reads


def create_operational_evidence(session: Session, payload: OperationalEvidenceCreate) -> OperationalEvidenceRead:
    if _get(session, Project, payload.project_id) is None:
        raise LookupError("Project not found")
    linked_requirement_ids = list(dict.fromkeys(payload.linked_requirement_ids))
    linked_verification_evidence_ids = list(dict.fromkeys(payload.linked_verification_evidence_ids))
    if not linked_requirement_ids and not linked_verification_evidence_ids:
        raise ValueError("Operational evidence must link to at least one requirement or verification evidence")
    if payload.coverage_window_end < payload.coverage_window_start:
        raise ValueError("Operational evidence coverage window end must be after the start")
    for requirement_id in linked_requirement_ids:
        _validate_operational_evidence_link(session, payload.project_id, OperationalEvidenceLinkObjectType.requirement, requirement_id)
    for verification_evidence_id in linked_verification_evidence_ids:
        _validate_operational_evidence_link(session, payload.project_id, OperationalEvidenceLinkObjectType.verification_evidence, verification_evidence_id)
    evidence = OperationalEvidence(**payload.model_dump(exclude={"linked_requirement_ids", "linked_verification_evidence_ids"}))
    link_rows: list[OperationalEvidenceLink] = []
    for requirement_id in linked_requirement_ids:
        link_rows.append(
            OperationalEvidenceLink(
                operational_evidence_id=evidence.id,
                internal_object_type=OperationalEvidenceLinkObjectType.requirement,
                internal_object_id=requirement_id,
            )
        )
    for verification_evidence_id in linked_verification_evidence_ids:
        link_rows.append(
            OperationalEvidenceLink(
                operational_evidence_id=evidence.id,
                internal_object_type=OperationalEvidenceLinkObjectType.verification_evidence,
                internal_object_id=verification_evidence_id,
            )
        )
    session.add(evidence)
    for link in link_rows:
        session.add(link)
    session.commit()
    session.refresh(evidence)
    return _operational_evidence_read(session, evidence, link_rows)


def get_operational_evidence_service(session: Session, evidence_id: UUID) -> OperationalEvidenceRead:
    evidence = _get(session, OperationalEvidence, evidence_id)
    if evidence is None:
        raise LookupError("Operational evidence not found")
    return _operational_evidence_read(session, evidence)


def seed_demo(session: Session) -> dict[str, Any]:
    project = _first_item(session.exec(select(Project).where(Project.code == "DRONE-001")))
    if project is None:
        project = _add(
            session,
            Project(
                code="DRONE-001",
                name="Inspection Drone MVP",
                description="Mission-driven drone demo that traces need -> design -> evidence -> change.",
                status=ProjectStatus.active,
            ),
        )

    reqs = {}
    for p in [
        {"project_id": project.id, "key": "DR-REQ-001", "title": "Drone shall fly for at least 30 minutes", "description": "Mission endurance target for the inspection route, with reserve for recovery.", "category": RequirementCategory.performance, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "verification_criteria_json": {"telemetry_thresholds": {"duration_minutes": {"min": 30}, "battery_consumption_pct": {"max": 85}}}, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-002", "title": "Drone shall stream real-time video to ground operator", "description": "Operator situational awareness requirement for the inspection mission.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-003", "title": "Drone shall operate between -5C and 40C", "description": "Environmental constraint derived from the intended mission profile.", "category": RequirementCategory.environment, "priority": Priority.high, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-004", "title": "Drone shall detect obstacles during low altitude flight", "description": "Safety requirement for the inspection route and landing approach.", "category": RequirementCategory.safety, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-005", "title": "Drone shall support remote monitoring of battery and mission status", "description": "Ground-control visibility requirement for mission health and endurance.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.demonstration, "status": RequirementStatus.draft, "version": 1, "verification_criteria_json": {"telemetry_thresholds": {"battery_consumption_pct": {"max": 85}}}},
        {"project_id": project.id, "key": "DR-REQ-006", "title": "Battery pack shall support mission reserve margin of 10 percent", "description": "Derived reserve requirement created from the endurance mission need.", "category": RequirementCategory.performance, "priority": Priority.medium, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.draft, "version": 1, "parent_requirement_id": None},
    ]:
        item = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == p["key"])))
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
        {"project_id": project.id, "key": "DR-BLK-001", "name": "Drone System", "description": "Mission-level architecture for the inspection drone.", "block_kind": BlockKind.system, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-002", "name": "Power Subsystem", "description": "Logical power architecture for endurance and reserve management.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-003", "name": "Propulsion Subsystem", "description": "Logical lift and propulsion architecture for the mission profile.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-004", "name": "Battery Pack", "description": "Physical battery assembly selected to support endurance.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-005", "name": "Flight Controller", "description": "Physical controller coordinating flight, telemetry, and safety behavior.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-006", "name": "Camera Module", "description": "Physical inspection payload for live video evidence.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.draft, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-007", "name": "Obstacle Detection Subsystem", "description": "Logical sensing and avoidance architecture for low-altitude safety.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
    ]:
        item = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == p["key"])))
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
        {"project_id": project.id, "key": "DR-CMP-001", "name": "Li-Ion Battery Pack", "description": "Physical battery pack sized for the endurance target.", "type": ComponentType.battery, "part_number": "BAT-3000", "supplier": "VoltCraft", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"capacity_mah": 12000}},
        {"project_id": project.id, "key": "DR-CMP-002", "name": "Brushless Motor Set", "description": "Physical lift motors used in the propulsion chain.", "type": ComponentType.motor, "part_number": "MTR-2208", "supplier": "AeroSpin", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"kv": 920}},
        {"project_id": project.id, "key": "DR-CMP-003", "name": "Flight Controller", "description": "Physical controller implementing mission behavior and telemetry.", "type": ComponentType.flight_controller, "part_number": "FC-REV2", "supplier": "SkyLogic", "status": ComponentStatus.validated, "version": 2, "metadata_json": {"firmware": "1.4.3"}},
        {"project_id": project.id, "key": "DR-CMP-004", "name": "Camera Module", "description": "Physical payload for the inspection video stream.", "type": ComponentType.camera, "part_number": "CAM-1080P", "supplier": "OptiView", "status": ComponentStatus.validated, "version": 1, "metadata_json": {"resolution": "1080p"}},
        {"project_id": project.id, "key": "DR-CMP-005", "name": "Obstacle Sensor", "description": "Physical sensing hardware for low-altitude obstacle detection.", "type": ComponentType.sensor, "part_number": "OBS-LIDAR-1", "supplier": "SenseWorks", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"range_m": 18}},
        {"project_id": project.id, "key": "DR-CMP-006", "name": "Flight Software", "description": "Software realization of autonomy, telemetry, and control.", "type": ComponentType.software_module, "part_number": "SW-FLT-1", "supplier": "ThreadLite Labs", "status": ComponentStatus.validated, "version": 3, "metadata_json": {"repository": "git@example.com:drone/flight.git", "branch": "main", "entry_point": "src/autonomy/main.py"}},
    ]:
        item = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == p["key"])))
        comps[p["key"]] = item or _add(session, Component.model_validate(p))

    tests = {}
    for p in [
        {"project_id": project.id, "key": "DR-TST-001", "title": "Flight Endurance Test", "description": "Verification step for the mission endurance target.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-002", "title": "Video Streaming Test", "description": "Verification step for operator video awareness.", "method": TestMethod.bench, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-003", "title": "Temperature Envelope Test", "description": "Simulation-based verification of environmental limits.", "method": TestMethod.simulation, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-004", "title": "Obstacle Detection Test", "description": "Verification step for low-altitude safety behavior.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
    ]:
        item = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == p["key"])))
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
            "summary": "Flight endurance evidence showing the mission falls short of the 30 minute target.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-001",
            "linked_requirement_ids": [reqs["DR-REQ-001"].id],
            "linked_test_case_ids": [tests["DR-TST-001"].id],
        },
        {
            "title": "Streaming verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Video stream evidence showing the operator view is available during the mission.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-002",
            "linked_requirement_ids": [reqs["DR-REQ-002"].id],
            "linked_test_case_ids": [tests["DR-TST-002"].id],
        },
        {
            "title": "Thermal simulation evidence",
            "evidence_type": VerificationEvidenceType.simulation,
            "summary": "Thermal simulation evidence showing the environment remains inside the declared envelope.",
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
            "summary": "Obstacle verification evidence showing low-altitude safety checks are in place.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-004",
            "linked_requirement_ids": [reqs["DR-REQ-004"].id],
            "linked_test_case_ids": [tests["DR-TST-004"].id],
        },
        {
            "title": "Flight software runtime evidence",
            "evidence_type": VerificationEvidenceType.telemetry,
            "summary": "Software telemetry evidence confirming the mission-control pipeline is active.",
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

    thermal_verification_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Thermal simulation evidence",
            )
        )
    )
    endurance_verification_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Endurance verification evidence",
            )
        )
    )
    fmi_contract = _first_item(
        session.exec(
            select(FMIContract).where(
                FMIContract.project_id == project.id,
                FMIContract.key == "FMI-THERMAL-001",
            )
        )
    )
    if fmi_contract is None:
        fmi_contract = _add(
            session,
            FMIContract(
                project_id=project.id,
                key="FMI-THERMAL-001",
                name="Thermal Envelope FMI Placeholder",
                description="Placeholder FMI-style contract for the endurance simulation model used in the mission narrative.",
                model_identifier="SIM-FLIGHT-ENDURANCE",
                model_version="1.4",
                model_uri="federation://SIM-FLIGHT-ENDURANCE",
                adapter_profile="simulink-placeholder",
                contract_version="fmi.placeholder.v1",
                metadata_json={"seeded": True, "adapter_capability": "simulation_metadata"},
            ),
        )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Thermal simulation result",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Thermal simulation result",
                model_reference="Endurance Model",
                scenario_name="Thermal envelope validation",
                input_summary="Ambient temperature sweep from -6C to 41C.",
                inputs_json={"ambient_low_c": -6, "ambient_high_c": 41},
                expected_behavior="Maintain thermal envelope and preserve margin.",
                observed_behavior="Simulation maintained the thermal envelope with 1.0C margin.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                fmi_contract_id=fmi_contract.id,
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL-ENVELOPE"},
                linked_requirement_ids=[reqs["DR-REQ-003"].id],
                linked_test_case_ids=[tests["DR-TST-003"].id],
                linked_verification_evidence_ids=[thermal_verification_evidence.id] if thermal_verification_evidence else [],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Endurance field evidence batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Endurance field evidence batch",
                source_name="Telemetry aggregator",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(minutes=22),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Aggregated field telemetry from the endurance mission and the resulting change trigger.",
                aggregated_observations_json={
                    "duration_minutes": 22,
                    "battery_consumption_pct": 88,
                    "altitude_m": 43,
                    "return_to_home": True,
                },
                quality_status=OperationalEvidenceQualityStatus.warning,
                derived_metrics_json={
                    "coverage_minutes": 22,
                    "low_battery_warning": True,
                },
                metadata_json={"contract_reference": "OP-EVBATCH:DR-RUN-001"},
                linked_requirement_ids=[reqs["DR-REQ-001"].id, reqs["DR-REQ-005"].id],
                linked_verification_evidence_ids=[endurance_verification_evidence.id] if endurance_verification_evidence else [],
            ),
        )

    run = _first_item(session.exec(select(OperationalRun).where(OperationalRun.project_id == project.id, OperationalRun.key == "DR-RUN-001")))
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

    cr = _first_item(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project.id, ChangeRequest.key == "CR-001")))
    if cr is None:
        cr = _add(session, ChangeRequest(project_id=project.id, key="CR-001", title="Increase battery endurance to support 35 minutes target", description="Change request raised after endurance evidence showed the mission stops short of the target. Investigate battery and propulsion changes to close the gap.", status=ChangeRequestStatus.open, severity=Severity.high))
    if not session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id)).first():
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-001"].id, impact_level=ImpactLevel.high, notes="Battery pack is the primary design driver behind the endurance gap."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-002"].id, impact_level=ImpactLevel.medium, notes="Motors affect power draw and endurance margin."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="requirement", object_id=reqs["DR-REQ-001"].id, impact_level=ImpactLevel.high, notes="Mission endurance requirement needs revision or decomposition."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="test_case", object_id=tests["DR-TST-001"].id, impact_level=ImpactLevel.medium, notes="Endurance verification test likely changes as the design is updated."))

    nc = _first_item(session.exec(select(NonConformity).where(NonConformity.project_id == project.id, NonConformity.key == "NC-001")))
    if nc is None:
        nc = _add(
            session,
            NonConformity(
                project_id=project.id,
                key="NC-001",
                title="Battery pack overheating during endurance run",
                description="Observed battery thermal excursion above nominal limits.",
                status=NonConformityStatus.analyzing,
                disposition=NonConformityDisposition.rework,
                review_comment="Investigate thermal mitigation before closing the deviation.",
                severity=Severity.high,
            ),
        )
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

    baseline = _first_item(session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Initial Drone Baseline")))
    if baseline is None:
        create_baseline(session, BaselineCreate(project_id=project.id, name="Initial Drone Baseline", description="Baseline for the seeded drone MVP."))

    connectors = {}
    for p in [
        {"name": "DOORS NG", "connector_type": ConnectorType.doors, "base_url": "https://doors.example.local", "description": "Requirement source system."},
        {"name": "Cameo MBSE", "connector_type": ConnectorType.sysml, "base_url": "https://cameo.example.local", "description": "SysML model source."},
        {"name": "Teamcenter PLM", "connector_type": ConnectorType.plm, "base_url": "https://teamcenter.example.local", "description": "Physical part source."},
        {"name": "Simulink Verification Export", "connector_type": ConnectorType.simulation, "base_url": "https://simulink.example.local", "description": "Simulation evidence export."},
    ]:
        connector = _first_item(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project.id, ConnectorDefinition.name == p["name"])))
        connectors[p["name"]] = connector or _add(session, ConnectorDefinition(project_id=project.id, name=p["name"], connector_type=p["connector_type"], base_url=p["base_url"], description=p["description"], is_active=True, metadata_json={"seeded": True}))

    artifacts = {}
    for p in [
        {"external_id": "REQ-DOORS-001", "artifact_type": ExternalArtifactType.requirement, "name": "Endurance requirement", "description": "Authoritative DOORS requirement for mission endurance.", "connector": "DOORS NG", "canonical_uri": "doors://REQ-DOORS-001", "native_tool_url": "https://doors.example.local/objects/REQ-DOORS-001"},
        {"external_id": "SYSML-BLOCK-BATTERY", "artifact_type": ExternalArtifactType.sysml_element, "name": "Battery Pack", "description": "Authoritative Cameo block for the battery assembly.", "connector": "Cameo MBSE", "canonical_uri": "sysml://SYSML-BLOCK-BATTERY", "native_tool_url": "https://cameo.example.local/elements/SYSML-BLOCK-BATTERY"},
        {"external_id": "PLM-PART-DR-BATT-01", "artifact_type": ExternalArtifactType.cad_part, "name": "Battery Pack Assembly", "description": "Authoritative Teamcenter part for the battery assembly.", "connector": "Teamcenter PLM", "canonical_uri": "plm://PLM-PART-DR-BATT-01", "native_tool_url": "https://teamcenter.example.local/items/PLM-PART-DR-BATT-01"},
        {"external_id": "SIM-FLIGHT-ENDURANCE", "artifact_type": ExternalArtifactType.simulation_model, "name": "Endurance Model", "description": "Simulink model used to validate endurance behavior.", "connector": "Simulink Verification Export", "canonical_uri": "federation://SIM-FLIGHT-ENDURANCE", "native_tool_url": "https://simulink.example.local/models/SIM-FLIGHT-ENDURANCE"},
    ]:
        artifact = _first_item(session.exec(select(ExternalArtifact).where(ExternalArtifact.project_id == project.id, ExternalArtifact.external_id == p["external_id"])))
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
        version = _first_item(session.exec(select(ExternalArtifactVersion).where(ExternalArtifactVersion.external_artifact_id == artifact.id, ExternalArtifactVersion.version_label == p["version_label"], ExternalArtifactVersion.revision_label == p["revision_label"])))
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

    context = _first_item(session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project.id, ConfigurationContext.key == "DRN-PDR-0.3")))
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


def seed_manufacturing_demo(session: Session) -> dict[str, Any]:
    base = _seed_profile_demo(
        session,
        code="MFG-001",
        name="Production Line Demo",
        description="Manufacturing demo that traces specifications to components, quality checks, evidence, and change.",
        profile="manufacturing",
        requirement_key="MFG-SPEC-001",
        requirement_title="Line shall maintain 99.5 percent fill accuracy",
        requirement_description="Quality specification for the production line's filled package accuracy and reject control.",
        requirement_category=RequirementCategory.performance,
        requirement_priority=Priority.critical,
        requirement_verification_method=VerificationMethod.test,
        block_key="MFG-BLK-001",
        block_name="Packaging Line",
        block_description="Top-level production line architecture for fill, inspect, and reject flow.",
        block_kind=BlockKind.system,
        block_abstraction_level=AbstractionLevel.logical,
        component_key="MFG-CMP-001",
        component_name="Fill Head Assembly",
        component_description="Physical fill head used to realize the accuracy target.",
        component_type=ComponentType.other,
        component_part_number="MFG-FILL-HEAD-01",
        component_supplier="PackRight",
        test_key="MFG-QC-001",
        test_title="Fill Accuracy Check",
        test_description="Quality check that validates production fill accuracy against specification.",
        test_method=TestMethod.inspection,
    )
    _seed_manufacturing_demo_details(session, UUID(base["project_id"]), base)
    return base


def seed_personal_demo(session: Session) -> dict[str, Any]:
    base = _seed_profile_demo(
        session,
        code="HOME-001",
        name="Home Infrastructure Demo",
        description="Personal demo that traces a goal to elements, evidence, and change.",
        profile="personal",
        requirement_key="HOME-GOAL-001",
        requirement_title="Home network shall keep backups available overnight",
        requirement_description="Personal goal for keeping backup copies online through the night and ready to restore.",
        requirement_category=RequirementCategory.performance,
        requirement_priority=Priority.high,
        requirement_verification_method=VerificationMethod.test,
        block_key="HOME-BLK-001",
        block_name="Home Network System",
        block_description="Top-level home network architecture supporting backup and isolation behavior.",
        block_kind=BlockKind.system,
        block_abstraction_level=AbstractionLevel.logical,
        component_key="HOME-CMP-001",
        component_name="Backup Storage Node",
        component_description="Home storage element used to realize the backup availability goal.",
        component_type=ComponentType.other,
        component_part_number="HOME-NAS-01",
        component_supplier="SyncedHome",
        test_key="HOME-VER-001",
        test_title="Overnight Backup Check",
        test_description="Verification check that the storage node remains reachable overnight.",
        test_method=TestMethod.inspection,
    )
    _seed_personal_demo_details(session, UUID(base["project_id"]), base)
    return base
