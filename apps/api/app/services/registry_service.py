"""Registry Service service layer for the DigitalThread API."""

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
from app.services.project_service import get_project_service
from app.services.block_service import list_blocks, list_block_containments
from app.services.requirement_service import list_requirements
from app.services.component_service import list_components
from app.services.federation_service import list_external_artifacts

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

__all__ = [
    "resolve_object",
    "summarize",
    "build_sysml_mapping_contract",
    "build_step_ap242_contract",
]
