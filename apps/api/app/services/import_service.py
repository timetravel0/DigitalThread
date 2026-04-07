"""Import Service service layer for the DigitalThread API."""

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

def import_project_records(session: Session, project_id: UUID, payload: ProjectImportCreate) -> ProjectImportResponse:
    from app.services.federation_service import create_external_artifact
    from app.services.evidence_service import create_verification_evidence

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

__all__ = [
    "import_project_records",
]
