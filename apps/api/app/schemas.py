from __future__ import annotations

from datetime import date as dt_date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models import *


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.draft


class ProjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(ProjectCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class RequirementBase(BaseModel):
    project_id: UUID
    key: str
    title: str
    description: str = ""
    category: RequirementCategory
    priority: Priority
    verification_method: VerificationMethod
    status: RequirementStatus = RequirementStatus.draft
    version: int = 1
    parent_requirement_id: UUID | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    category: RequirementCategory | None = None
    priority: Priority | None = None
    verification_method: VerificationMethod | None = None
    status: RequirementStatus | None = None
    version: int | None = None
    parent_requirement_id: UUID | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class RequirementRead(RequirementBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BlockBase(BaseModel):
    project_id: UUID
    key: str
    name: str
    description: str = ""
    block_kind: BlockKind
    abstraction_level: AbstractionLevel
    status: BlockStatus = BlockStatus.draft
    version: int = 1
    owner: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class BlockCreate(BlockBase):
    pass


class BlockUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None
    block_kind: BlockKind | None = None
    abstraction_level: AbstractionLevel | None = None
    status: BlockStatus | None = None
    version: int | None = None
    owner: str | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class BlockRead(BlockBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BlockContainmentCreate(BaseModel):
    project_id: UUID
    parent_block_id: UUID
    child_block_id: UUID
    relation_type: BlockContainmentRelationType = BlockContainmentRelationType.contains


class BlockContainmentRead(BlockContainmentCreate, ORMBase):
    id: UUID
    created_at: datetime


class ComponentCreate(BaseModel):
    project_id: UUID
    key: str
    name: str
    description: str = ""
    type: ComponentType
    part_number: str | None = None
    supplier: str | None = None
    status: ComponentStatus = ComponentStatus.draft
    version: int = 1
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ComponentUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None
    type: ComponentType | None = None
    part_number: str | None = None
    supplier: str | None = None
    status: ComponentStatus | None = None
    version: int | None = None
    metadata_json: dict[str, Any] | None = None


class ComponentRead(ComponentCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class TestCaseBase(BaseModel):
    project_id: UUID
    key: str
    title: str
    description: str = ""
    method: TestMethod
    status: TestCaseStatus = TestCaseStatus.draft
    version: int = 1
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    method: TestMethod | None = None
    status: TestCaseStatus | None = None
    version: int | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    rejection_reason: str | None = None
    review_comment: str | None = None


class TestCaseRead(TestCaseBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class TestRunCreate(BaseModel):
    test_case_id: UUID
    execution_date: dt_date
    result: TestRunResult
    summary: str = ""
    measured_values_json: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""
    executed_by: str | None = None


class TestRunRead(TestRunCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class VerificationEvidenceBase(BaseModel):
    project_id: UUID
    title: str
    evidence_type: VerificationEvidenceType
    summary: str = ""
    observed_at: datetime | None = None
    source_name: str | None = None
    source_reference: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class VerificationEvidenceCreate(VerificationEvidenceBase):
    linked_requirement_ids: list[UUID] = Field(default_factory=list)
    linked_test_case_ids: list[UUID] = Field(default_factory=list)
    linked_component_ids: list[UUID] = Field(default_factory=list)
    linked_non_conformity_ids: list[UUID] = Field(default_factory=list)


class VerificationEvidenceRead(VerificationEvidenceBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    linked_objects: list[ObjectSummary] = Field(default_factory=list)


class FMIContractBase(BaseModel):
    project_id: UUID
    key: str
    name: str
    description: str = ""
    model_identifier: str
    model_version: str | None = None
    model_uri: str | None = None
    adapter_profile: str | None = None
    contract_version: str = "fmi.placeholder.v1"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class FMIContractCreate(FMIContractBase):
    pass


class FMIContractUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    name: str | None = None
    description: str | None = None
    model_identifier: str | None = None
    model_version: str | None = None
    model_uri: str | None = None
    adapter_profile: str | None = None
    contract_version: str | None = None
    metadata_json: dict[str, Any] | None = None


class FMIContractRead(FMIContractBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    linked_simulation_evidence_count: int = 0


class FMIContractDetail(BaseModel):
    fmi_contract: FMIContractRead
    simulation_evidence: list["SimulationEvidenceRead"] = Field(default_factory=list)


class SimulationEvidenceBase(BaseModel):
    project_id: UUID
    title: str
    model_reference: str
    scenario_name: str
    input_summary: str | None = None
    inputs_json: dict[str, Any] = Field(default_factory=dict)
    expected_behavior: str = ""
    observed_behavior: str = ""
    result: SimulationEvidenceResult
    execution_timestamp: datetime
    fmi_contract_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SimulationEvidenceCreate(SimulationEvidenceBase):
    linked_requirement_ids: list[UUID] = Field(default_factory=list)
    linked_test_case_ids: list[UUID] = Field(default_factory=list)
    linked_verification_evidence_ids: list[UUID] = Field(default_factory=list)


class SimulationEvidenceRead(SimulationEvidenceBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    linked_objects: list[ObjectSummary] = Field(default_factory=list)
    fmi_contract_key: str | None = None
    fmi_contract_name: str | None = None
    fmi_contract_model_identifier: str | None = None
    fmi_contract_model_version: str | None = None
    fmi_contract_contract_version: str | None = None


class SimulationEvidenceLinkRead(ORMBase):
    id: UUID
    simulation_evidence_id: UUID
    internal_object_type: SimulationEvidenceLinkObjectType
    internal_object_id: UUID
    created_at: datetime


class OperationalEvidenceBase(BaseModel):
    project_id: UUID
    title: str
    source_name: str
    source_type: OperationalEvidenceSourceType
    captured_at: datetime
    coverage_window_start: datetime
    coverage_window_end: datetime
    observations_summary: str = ""
    aggregated_observations_json: dict[str, Any] = Field(default_factory=dict)
    quality_status: OperationalEvidenceQualityStatus
    derived_metrics_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class OperationalEvidenceCreate(OperationalEvidenceBase):
    linked_requirement_ids: list[UUID] = Field(default_factory=list)
    linked_verification_evidence_ids: list[UUID] = Field(default_factory=list)


class OperationalEvidenceRead(OperationalEvidenceBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    linked_objects: list[ObjectSummary] = Field(default_factory=list)


class OperationalEvidenceLinkRead(ORMBase):
    id: UUID
    operational_evidence_id: UUID
    internal_object_type: OperationalEvidenceLinkObjectType
    internal_object_id: UUID
    created_at: datetime


class ComponentDetail(BaseModel):
    component: ComponentRead
    links: list[LinkRead] = Field(default_factory=list)
    verification_evidence: list[VerificationEvidenceRead] = Field(default_factory=list)
    impact: ImpactResponse
    change_impacts: list[ChangeImpactRead] = Field(default_factory=list)


class OperationalRunCreate(BaseModel):
    project_id: UUID
    key: str
    date: dt_date
    drone_serial: str
    location: str
    duration_minutes: int
    max_temperature_c: float | None = None
    battery_consumption_pct: float | None = None
    outcome: OperationalOutcome
    notes: str = ""
    telemetry_json: dict[str, Any] = Field(default_factory=dict)


class OperationalRunUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    date: dt_date | None = None
    drone_serial: str | None = None
    location: str | None = None
    duration_minutes: int | None = None
    max_temperature_c: float | None = None
    battery_consumption_pct: float | None = None
    outcome: OperationalOutcome | None = None
    notes: str | None = None
    telemetry_json: dict[str, Any] | None = None


class OperationalRunRead(OperationalRunCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class OperationalRunDetail(BaseModel):
    operational_run: OperationalRunRead
    links: list[LinkRead] = Field(default_factory=list)
    impact: ImpactResponse


class BaselineCreate(BaseModel):
    project_id: UUID
    name: str
    description: str = ""
    status: BaselineStatus = BaselineStatus.draft
    requirement_ids: list[UUID] = Field(default_factory=list)
    block_ids: list[UUID] = Field(default_factory=list)
    test_case_ids: list[UUID] = Field(default_factory=list)
    include_unapproved: bool = False


class BaselineRead(BaselineCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class BaselineDetailRead(BaseModel):
    baseline: BaselineRead
    bridge_context: BaselineBridgeContextRead
    items: list[BaselineItemRead] = Field(default_factory=list)
    related_configuration_contexts: list[ConfigurationContextRead] = Field(default_factory=list)


class RequirementDetail(BaseModel):
    requirement: RequirementRead
    links: list[LinkRead] = Field(default_factory=list)
    artifact_links: list[ArtifactLinkRead] = Field(default_factory=list)
    verification_evidence: list[VerificationEvidenceRead] = Field(default_factory=list)
    simulation_evidence: list[SimulationEvidenceRead] = Field(default_factory=list)
    verification_evaluation: RequirementVerificationEvaluation
    history: list[RevisionSnapshotRead] = Field(default_factory=list)
    impact: ImpactResponse


class TestCaseDetail(BaseModel):
    test_case: TestCaseRead
    links: list[LinkRead] = Field(default_factory=list)
    artifact_links: list[ArtifactLinkRead] = Field(default_factory=list)
    verification_evidence: list[VerificationEvidenceRead] = Field(default_factory=list)
    simulation_evidence: list[SimulationEvidenceRead] = Field(default_factory=list)
    runs: list[TestRunRead] = Field(default_factory=list)
    history: list[RevisionSnapshotRead] = Field(default_factory=list)
    impact: ImpactResponse


class RequirementVerificationEvaluation(BaseModel):
    status: RequirementVerificationStatus
    decision_source: str = ""
    decision_summary: str = ""
    linked_evidence_count: int = 0
    fresh_evidence_count: int = 0
    stale_evidence_count: int = 0
    linked_operational_run_count: int = 0
    fresh_operational_run_count: int = 0
    stale_operational_run_count: int = 0
    successful_operational_run_count: int = 0
    degraded_operational_run_count: int = 0
    failed_operational_run_count: int = 0
    linked_test_case_count: int = 0
    passed_test_case_count: int = 0
    partial_test_case_count: int = 0
    failed_test_case_count: int = 0
    reasons: list[str] = Field(default_factory=list)


class VerificationStatusBreakdown(BaseModel):
    verified: int = 0
    partially_verified: int = 0
    at_risk: int = 0
    failed: int = 0
    not_covered: int = 0


class BaselineItemRead(ORMBase):
    id: UUID
    baseline_id: UUID
    object_type: BaselineObjectType
    object_id: UUID
    object_version: int


class LinkCreate(BaseModel):
    project_id: UUID
    source_type: LinkObjectType
    source_id: UUID
    target_type: LinkObjectType
    target_id: UUID
    relation_type: RelationType
    rationale: str | None = None


class LinkRead(LinkCreate, ORMBase):
    id: UUID
    created_at: datetime
    source_label: str | None = None
    target_label: str | None = None


class SysMLRelationCreate(BaseModel):
    project_id: UUID
    source_type: SysMLObjectType
    source_id: UUID
    target_type: SysMLObjectType
    target_id: UUID
    relation_type: SysMLRelationType
    rationale: str | None = None


class SysMLRelationRead(SysMLRelationCreate, ORMBase):
    id: UUID
    created_at: datetime


class RevisionSnapshotRead(ORMBase):
    id: UUID
    project_id: UUID
    object_type: str
    object_id: UUID
    version: int
    snapshot_json: dict[str, Any]
    snapshot_hash: str | None = None
    previous_snapshot_hash: str | None = None
    changed_at: datetime
    changed_by: str | None = None
    change_summary: str | None = None


class ApprovalActionLogRead(ORMBase):
    id: UUID
    project_id: UUID
    object_type: str
    object_id: UUID
    from_status: str
    to_status: str
    action: str
    actor: str | None = None
    comment: str | None = None
    created_at: datetime


class WorkflowActionPayload(BaseModel):
    actor: str | None = None
    comment: str | None = None
    reason: str | None = None
    change_summary: str | None = None


class ChangeRequestCreate(BaseModel):
    project_id: UUID
    key: str
    title: str
    description: str = ""
    status: ChangeRequestStatus = ChangeRequestStatus.open
    severity: Severity


class ChangeRequestUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    status: ChangeRequestStatus | None = None
    severity: Severity | None = None


class ChangeRequestRead(ChangeRequestCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ChangeRequestDetail(BaseModel):
    change_request: ChangeRequestRead
    impacts: list[ChangeImpactRead] = Field(default_factory=list)
    impact_summary: list[ObjectSummary] = Field(default_factory=list)
    history: list[ApprovalActionLogRead] = Field(default_factory=list)


class NonConformityDetail(BaseModel):
    non_conformity: NonConformityRead
    links: list[LinkRead] = Field(default_factory=list)
    related_requirements: list[ObjectSummary] = Field(default_factory=list)
    verification_evidence: list[VerificationEvidenceRead] = Field(default_factory=list)
    impact: ImpactResponse
    impact_summary: list[ObjectSummary] = Field(default_factory=list)


class NonConformityBase(BaseModel):
    project_id: UUID
    key: str
    title: str
    description: str = ""
    status: NonConformityStatus = NonConformityStatus.detected
    disposition: NonConformityDisposition | None = None
    review_comment: str | None = None
    severity: Severity


class NonConformityCreate(NonConformityBase):
    pass


class NonConformityUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    status: NonConformityStatus | None = None
    disposition: NonConformityDisposition | None = None
    review_comment: str | None = None
    severity: Severity | None = None


class NonConformityRead(NonConformityBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ChangeImpactCreate(BaseModel):
    change_request_id: UUID
    object_type: str
    object_id: UUID
    impact_level: ImpactLevel
    notes: str = ""


class ChangeImpactRead(ChangeImpactCreate, ORMBase):
    id: UUID


class ConnectorDefinitionBase(BaseModel):
    project_id: UUID
    name: str
    connector_type: ConnectorType
    base_url: str | None = None
    description: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None


class ConnectorDefinitionCreate(ConnectorDefinitionBase):
    pass


class ConnectorDefinitionUpdate(BaseModel):
    name: str | None = None
    connector_type: ConnectorType | None = None
    base_url: str | None = None
    description: str | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class ConnectorDefinitionRead(ConnectorDefinitionBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    artifact_count: int = 0


class ExternalArtifactBase(BaseModel):
    project_id: UUID
    connector_definition_id: UUID | None = None
    external_id: str
    artifact_type: ExternalArtifactType
    name: str
    description: str | None = None
    canonical_uri: str | None = None
    native_tool_url: str | None = None
    status: ExternalArtifactStatus = ExternalArtifactStatus.active
    metadata_json: dict[str, Any] | None = None


class ExternalArtifactCreate(ExternalArtifactBase):
    pass


class ExternalArtifactUpdate(BaseModel):
    connector_definition_id: UUID | None = None
    external_id: str | None = None
    artifact_type: ExternalArtifactType | None = None
    name: str | None = None
    description: str | None = None
    canonical_uri: str | None = None
    native_tool_url: str | None = None
    status: ExternalArtifactStatus | None = None
    metadata_json: dict[str, Any] | None = None


class ExternalArtifactVersionCreate(BaseModel):
    version_label: str
    revision_label: str | None = None
    checksum_or_signature: str | None = None
    effective_date: dt_date | None = None
    source_timestamp: datetime | None = None
    metadata_json: dict[str, Any] | None = None


class ExternalArtifactVersionRead(ExternalArtifactVersionCreate, ORMBase):
    id: UUID
    external_artifact_id: UUID
    created_at: datetime


class ExternalArtifactRead(ExternalArtifactBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    connector_name: str | None = None
    connector_type: ConnectorType | None = None
    versions: list[ExternalArtifactVersionRead] = Field(default_factory=list)


class ImportFormat(str, Enum):
    json = "json"
    csv = "csv"


class ProjectImportCreate(BaseModel):
    format: ImportFormat
    content: str


class ProjectImportSummary(BaseModel):
    parsed_records: int = 0
    created_external_artifacts: int = 0
    created_verification_evidence: int = 0


class ProjectImportResponse(BaseModel):
    project: ProjectRead
    summary: ProjectImportSummary
    external_artifacts: list[ExternalArtifactRead] = Field(default_factory=list)
    verification_evidence: list[VerificationEvidenceRead] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ArtifactLinkCreate(BaseModel):
    project_id: UUID
    internal_object_type: FederatedInternalObjectType
    internal_object_id: UUID
    external_artifact_id: UUID
    external_artifact_version_id: UUID | None = None
    relation_type: ArtifactLinkRelationType
    rationale: str | None = None


class ArtifactLinkRead(ArtifactLinkCreate, ORMBase):
    id: UUID
    created_at: datetime
    internal_object_label: str | None = None
    external_artifact_name: str | None = None
    external_artifact_version_label: str | None = None
    connector_name: str | None = None


class ConfigurationContextBase(BaseModel):
    project_id: UUID
    key: str
    name: str
    description: str | None = None
    context_type: ConfigurationContextType = ConfigurationContextType.working
    status: ConfigurationContextStatus = ConfigurationContextStatus.draft


class ConfigurationContextCreate(ConfigurationContextBase):
    pass


class ConfigurationContextUpdate(BaseModel):
    key: str | None = None
    name: str | None = None
    description: str | None = None
    context_type: ConfigurationContextType | None = None
    status: ConfigurationContextStatus | None = None


class ConfigurationContextRead(ConfigurationContextBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class BaselineBridgeContextRead(ConfigurationContextRead):
    baseline_id: UUID
    baseline_name: str


class ConfigurationContextComparisonEntry(BaseModel):
    item_kind: ConfigurationItemKind
    label: str
    object_type: str | None = None
    object_id: UUID | None = None
    object_version: int | None = None
    external_artifact_id: UUID | None = None
    external_artifact_version_id: UUID | None = None
    version_label: str | None = None
    revision_label: str | None = None
    connector_name: str | None = None
    artifact_name: str | None = None
    artifact_type: str | None = None
    role_label: str | None = None
    notes: str | None = None


class ConfigurationContextComparisonChange(BaseModel):
    key: str
    left: ConfigurationContextComparisonEntry | None = None
    right: ConfigurationContextComparisonEntry | None = None


class ConfigurationContextComparisonGroup(BaseModel):
    item_kind: ConfigurationItemKind
    added: list[ConfigurationContextComparisonEntry] = Field(default_factory=list)
    removed: list[ConfigurationContextComparisonEntry] = Field(default_factory=list)
    version_changed: list[ConfigurationContextComparisonChange] = Field(default_factory=list)


class ConfigurationContextComparisonSummary(BaseModel):
    added: int = 0
    removed: int = 0
    version_changed: int = 0


class ConfigurationContextComparisonResponse(BaseModel):
    left_context: ConfigurationContextRead
    right_context: ConfigurationContextRead
    summary: ConfigurationContextComparisonSummary
    groups: list[ConfigurationContextComparisonGroup]


class BaselineContextComparisonResponse(BaseModel):
    baseline: BaselineRead
    configuration_context: ConfigurationContextRead
    summary: ConfigurationContextComparisonSummary
    groups: list[ConfigurationContextComparisonGroup]


class BaselineComparisonResponse(BaseModel):
    left_baseline: BaselineRead
    right_baseline: BaselineRead
    summary: ConfigurationContextComparisonSummary
    groups: list[ConfigurationContextComparisonGroup]


class ConfigurationItemMappingCreate(BaseModel):
    item_kind: ConfigurationItemKind
    internal_object_type: FederatedInternalObjectType | None = None
    internal_object_id: UUID | None = None
    internal_object_version: int | None = None
    external_artifact_version_id: UUID | None = None
    role_label: str | None = None
    notes: str | None = None


class ConfigurationItemMappingRead(ConfigurationItemMappingCreate, ORMBase):
    id: UUID
    configuration_context_id: UUID
    created_at: datetime


class AuthoritativeRegistrySummary(BaseModel):
    connectors: int = 0
    external_artifacts: int = 0
    external_artifact_versions: int = 0
    artifact_links: int = 0
    configuration_contexts: int = 0
    configuration_item_mappings: int = 0


class ObjectSummary(BaseModel):
    object_type: str
    object_id: UUID
    label: str
    code: str | None = None
    status: str | None = None
    version: int | None = None


class DashboardKpis(BaseModel):
    total_requirements: int
    requirements_with_allocated_components: int
    requirements_with_verifying_tests: int
    requirements_at_risk: int
    failed_tests_last_30_days: int
    open_change_requests: int


class ProjectDashboard(BaseModel):
    project: ProjectRead
    kpis: DashboardKpis
    verification_status_breakdown: VerificationStatusBreakdown
    recent_test_runs: list[TestRunRead]
    recent_changes: list[ChangeRequestRead]
    recent_links: list[LinkRead]


class GlobalDashboard(BaseModel):
    projects: list[ProjectRead]
    kpis: DashboardKpis
    verification_status_breakdown: VerificationStatusBreakdown
    recent_test_runs: list[TestRunRead]
    recent_changes: list[ChangeRequestRead]
    recent_links: list[LinkRead]


class MatrixColumn(BaseModel):
    object_type: LinkObjectType
    object_id: UUID
    label: str
    code: str | None = None
    status: str | None = None


class MatrixRow(BaseModel):
    requirement: RequirementRead


class MatrixCell(BaseModel):
    row_requirement_id: UUID
    column_object_type: LinkObjectType
    column_object_id: UUID
    linked: bool
    relation_types: list[RelationType] = Field(default_factory=list)
    link_ids: list[UUID] = Field(default_factory=list)


class MatrixResponse(BaseModel):
    project: ProjectRead
    mode: str
    requirement_filters: dict[str, str | None]
    rows: list[MatrixRow]
    columns: list[MatrixColumn]
    cells: list[MatrixCell]


class ImpactResponse(BaseModel):
    project: ProjectRead
    object: ObjectSummary
    direct: list[ObjectSummary]
    secondary: list[ObjectSummary]
    likely_impacted: list[ObjectSummary]
    links: list[LinkRead]
    related_baselines: list[BaselineRead] = Field(default_factory=list)
    open_change_requests: list[ChangeRequestRead] = Field(default_factory=list)


class BlockTreeNode(BaseModel):
    block: BlockRead
    children: list["BlockTreeNode"] = Field(default_factory=list)
    satisfied_requirements: list[ObjectSummary] = Field(default_factory=list)
    linked_tests: list[ObjectSummary] = Field(default_factory=list)


class SatisfactionRow(BaseModel):
    block: BlockRead
    requirements: list[ObjectSummary] = Field(default_factory=list)


class VerificationRow(BaseModel):
    test_case: TestCaseRead
    requirements: list[ObjectSummary] = Field(default_factory=list)


class DerivationRow(BaseModel):
    source_requirement: RequirementRead
    derived_requirements: list[ObjectSummary] = Field(default_factory=list)


class SysMLTreeResponse(BaseModel):
    project: ProjectRead
    roots: list[BlockTreeNode]


class SysMLSatisfactionResponse(BaseModel):
    project: ProjectRead
    rows: list[SatisfactionRow]


class SysMLVerificationResponse(BaseModel):
    project: ProjectRead
    rows: list[VerificationRow]


class SysMLDerivationResponse(BaseModel):
    project: ProjectRead
    rows: list[DerivationRow]


class SysMLMappingSummary(BaseModel):
    requirement_count: int
    block_count: int
    logical_block_count: int
    physical_block_count: int
    satisfy_relation_count: int
    verify_relation_count: int
    derive_relation_count: int
    contain_relation_count: int


class SysMLRequirementMappingRow(BaseModel):
    requirement: RequirementRead
    sysml_concept: str = "requirement"
    satisfy_blocks: list[ObjectSummary] = Field(default_factory=list)
    verify_tests: list[ObjectSummary] = Field(default_factory=list)
    derived_from: list[ObjectSummary] = Field(default_factory=list)
    derived_requirements: list[ObjectSummary] = Field(default_factory=list)


class SysMLBlockMappingRow(BaseModel):
    block: BlockRead
    sysml_concept: str = "block"
    abstraction_level: AbstractionLevel
    profile_label: str
    contained_blocks: list[ObjectSummary] = Field(default_factory=list)
    contained_in: list[ObjectSummary] = Field(default_factory=list)
    satisfies_requirements: list[ObjectSummary] = Field(default_factory=list)


class SysMLMappingRelationRow(BaseModel):
    relation_type: str
    source: ObjectSummary
    target: ObjectSummary
    semantics: str


class SysMLMappingContractResponse(BaseModel):
    contract_schema: str = "threadlite.sysml.mapping-contract.v1"
    project: ProjectRead
    generated_at: datetime
    summary: SysMLMappingSummary
    requirements: list[SysMLRequirementMappingRow]
    blocks: list[SysMLBlockMappingRow]
    relations: list[SysMLMappingRelationRow]


class STEPAP242Summary(BaseModel):
    physical_component_count: int
    cad_artifact_count: int
    linked_cad_artifact_count: int
    identifier_count: int


class STEPAP242IdentifierRow(BaseModel):
    kind: str
    value: str
    source: str


class STEPAP242PartRow(BaseModel):
    component: ComponentRead
    part_number: str | None = None
    version: int
    status: str
    supplier: str | None = None
    profile_label: str = "Physical part"
    identifiers: list[STEPAP242IdentifierRow] = Field(default_factory=list)
    linked_cad_artifacts: list[ExternalArtifactRead] = Field(default_factory=list)


class STEPAP242RelationRow(BaseModel):
    relation_type: str
    component: ObjectSummary
    cad_artifact: ExternalArtifactRead
    semantics: str


class STEPAP242ContractResponse(BaseModel):
    contract_schema: str = "threadlite.step.ap242.contract.v1"
    project: ProjectRead
    generated_at: datetime
    summary: STEPAP242Summary
    parts: list[STEPAP242PartRow]
    cad_artifacts: list[ExternalArtifactRead]
    relations: list[STEPAP242RelationRow]


class ReviewQueueItem(BaseModel):
    object_type: str
    id: UUID
    key: str
    title: str
    status: str
    version: int
    updated_at: datetime


class ReviewQueueResponse(BaseModel):
    project: ProjectRead
    items: list[ReviewQueueItem]
