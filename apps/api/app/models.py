from __future__ import annotations

from datetime import date as dt_date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, JSON, String
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectStatus(str, Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class RequirementCategory(str, Enum):
    performance = "performance"
    safety = "safety"
    environment = "environment"
    operations = "operations"
    compliance = "compliance"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class VerificationMethod(str, Enum):
    analysis = "analysis"
    inspection = "inspection"
    test = "test"
    demonstration = "demonstration"


class RequirementStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    implemented = "implemented"
    verified = "verified"
    failed = "failed"
    obsolete = "obsolete"
    retired = "retired"


class RequirementVerificationStatus(str, Enum):
    not_covered = "not_covered"
    partially_verified = "partially_verified"
    at_risk = "at_risk"
    failed = "failed"
    verified = "verified"


class BlockKind(str, Enum):
    system = "system"
    subsystem = "subsystem"
    assembly = "assembly"
    component = "component"
    software = "software"
    interface = "interface"
    other = "other"


class AbstractionLevel(str, Enum):
    logical = "logical"
    physical = "physical"


class BlockStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    obsolete = "obsolete"


class ComponentType(str, Enum):
    battery = "battery"
    motor = "motor"
    flight_controller = "flight_controller"
    camera = "camera"
    sensor = "sensor"
    frame = "frame"
    software_module = "software_module"
    other = "other"


class ComponentStatus(str, Enum):
    draft = "draft"
    selected = "selected"
    validated = "validated"
    retired = "retired"


class TestMethod(str, Enum):
    bench = "bench"
    simulation = "simulation"
    field = "field"
    inspection = "inspection"


class TestCaseStatus(str, Enum):
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    ready = "ready"
    executed = "executed"
    failed = "failed"
    passed = "passed"
    archived = "archived"
    obsolete = "obsolete"


class TestRunResult(str, Enum):
    passed = "passed"
    failed = "failed"
    partial = "partial"


class OperationalOutcome(str, Enum):
    success = "success"
    degraded = "degraded"
    failure = "failure"


class VerificationEvidenceType(str, Enum):
    test_result = "test_result"
    simulation = "simulation"
    telemetry = "telemetry"
    analysis = "analysis"
    inspection = "inspection"
    other = "other"


class BaselineStatus(str, Enum):
    draft = "draft"
    released = "released"
    obsolete = "obsolete"


class BaselineObjectType(str, Enum):
    requirement = "requirement"
    block = "block"
    component = "component"
    test_case = "test_case"


class LinkObjectType(str, Enum):
    requirement = "requirement"
    component = "component"
    test_case = "test_case"
    test_run = "test_run"
    operational_run = "operational_run"
    change_request = "change_request"
    non_conformity = "non_conformity"


class RelationType(str, Enum):
    satisfies = "satisfies"
    allocated_to = "allocated_to"
    verifies = "verifies"
    tested_by = "tested_by"
    impacts = "impacts"
    derived_from = "derived_from"
    depends_on = "depends_on"
    uses = "uses"
    reports_on = "reports_on"
    validates = "validates"
    fails = "fails"


class SysMLObjectType(str, Enum):
    requirement = "requirement"
    block = "block"
    test_case = "test_case"
    component = "component"
    operational_run = "operational_run"


class SysMLRelationType(str, Enum):
    satisfy = "satisfy"
    verify = "verify"
    deriveReqt = "deriveReqt"
    refine = "refine"
    trace = "trace"
    allocate = "allocate"
    contain = "contain"


class BlockContainmentRelationType(str, Enum):
    contains = "contains"
    composed_of = "composed_of"


class ChangeRequestStatus(str, Enum):
    open = "open"
    analysis = "analysis"
    approved = "approved"
    rejected = "rejected"
    implemented = "implemented"
    closed = "closed"


class NonConformityStatus(str, Enum):
    detected = "detected"
    analyzing = "analyzing"
    contained = "contained"
    corrected = "corrected"
    verified = "verified"
    closed = "closed"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ImpactLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ConnectorType(str, Enum):
    doors = "doors"
    sysml = "sysml"
    plm = "plm"
    simulation = "simulation"
    test = "test"
    telemetry = "telemetry"
    custom = "custom"


class ExternalArtifactType(str, Enum):
    requirement = "requirement"
    sysml_element = "sysml_element"
    block = "block"
    cad_part = "cad_part"
    software_module = "software_module"
    test_case = "test_case"
    simulation_model = "simulation_model"
    test_result = "test_result"
    telemetry_source = "telemetry_source"
    document = "document"
    other = "other"


class ExternalArtifactStatus(str, Enum):
    active = "active"
    deprecated = "deprecated"
    obsolete = "obsolete"


class FederatedInternalObjectType(str, Enum):
    project = "project"
    requirement = "requirement"
    block = "block"
    test_case = "test_case"
    baseline = "baseline"
    change_request = "change_request"
    non_conformity = "non_conformity"
    component = "component"


class ArtifactLinkRelationType(str, Enum):
    authoritative_reference = "authoritative_reference"
    derived_from_external = "derived_from_external"
    synchronized_with = "synchronized_with"
    validated_against = "validated_against"
    exported_to = "exported_to"
    maps_to = "maps_to"


class ConfigurationContextType(str, Enum):
    working = "working"
    baseline_candidate = "baseline_candidate"
    review_gate = "review_gate"
    released = "released"
    imported = "imported"


class ConfigurationContextStatus(str, Enum):
    draft = "draft"
    active = "active"
    frozen = "frozen"
    obsolete = "obsolete"


class ConfigurationItemKind(str, Enum):
    internal_requirement = "internal_requirement"
    internal_block = "internal_block"
    internal_test_case = "internal_test_case"
    baseline_item = "baseline_item"
    external_artifact_version = "external_artifact_version"


class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)


class Project(TimestampMixin, SQLModel, table=True):
    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    code: str = Field(sa_column=Column(String(64), unique=True, index=True, nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    status: ProjectStatus = Field(default=ProjectStatus.draft, sa_column=Column(SAEnum(ProjectStatus), nullable=False))


class Requirement(TimestampMixin, SQLModel, table=True):
    __tablename__ = "requirements"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    category: RequirementCategory = Field(sa_column=Column(SAEnum(RequirementCategory), nullable=False))
    priority: Priority = Field(sa_column=Column(SAEnum(Priority), nullable=False))
    verification_method: VerificationMethod = Field(sa_column=Column(SAEnum(VerificationMethod), nullable=False))
    status: RequirementStatus = Field(default=RequirementStatus.draft, sa_column=Column(SAEnum(RequirementStatus), nullable=False))
    version: int = Field(default=1, nullable=False)
    parent_requirement_id: UUID | None = Field(default=None, foreign_key="requirements.id", index=True)
    approved_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    approved_by: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    rejection_reason: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    review_comment: str | None = Field(default=None, sa_column=Column(String, nullable=True))


class Block(TimestampMixin, SQLModel, table=True):
    __tablename__ = "blocks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    block_kind: BlockKind = Field(sa_column=Column(SAEnum(BlockKind), nullable=False))
    abstraction_level: AbstractionLevel = Field(sa_column=Column(SAEnum(AbstractionLevel), nullable=False))
    status: BlockStatus = Field(default=BlockStatus.draft, sa_column=Column(SAEnum(BlockStatus), nullable=False))
    version: int = Field(default=1, nullable=False)
    owner: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    approved_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    approved_by: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    rejection_reason: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    review_comment: str | None = Field(default=None, sa_column=Column(String, nullable=True))


class BlockContainment(SQLModel, table=True):
    __tablename__ = "block_containments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    parent_block_id: UUID = Field(foreign_key="blocks.id", index=True)
    child_block_id: UUID = Field(foreign_key="blocks.id", index=True)
    relation_type: BlockContainmentRelationType = Field(sa_column=Column(SAEnum(BlockContainmentRelationType), nullable=False))
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class Component(TimestampMixin, SQLModel, table=True):
    __tablename__ = "components"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    type: ComponentType = Field(sa_column=Column(SAEnum(ComponentType), nullable=False))
    part_number: str | None = Field(default=None)
    supplier: str | None = Field(default=None)
    status: ComponentStatus = Field(default=ComponentStatus.draft, sa_column=Column(SAEnum(ComponentStatus), nullable=False))
    version: int = Field(default=1, nullable=False)
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class TestCase(TimestampMixin, SQLModel, table=True):
    __tablename__ = "test_cases"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    method: TestMethod = Field(sa_column=Column(SAEnum(TestMethod), nullable=False))
    status: TestCaseStatus = Field(default=TestCaseStatus.draft, sa_column=Column(SAEnum(TestCaseStatus), nullable=False))
    version: int = Field(default=1, nullable=False)
    approved_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    approved_by: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    rejection_reason: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    review_comment: str | None = Field(default=None, sa_column=Column(String, nullable=True))


class TestRun(TimestampMixin, SQLModel, table=True):
    __tablename__ = "test_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    test_case_id: UUID = Field(foreign_key="test_cases.id", index=True)
    execution_date: dt_date = Field(nullable=False)
    result: TestRunResult = Field(sa_column=Column(SAEnum(TestRunResult), nullable=False))
    summary: str = Field(default="", nullable=False)
    measured_values_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    notes: str = Field(default="", nullable=False)
    executed_by: str | None = Field(default=None)


class OperationalRun(TimestampMixin, SQLModel, table=True):
    __tablename__ = "operational_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    date: dt_date = Field(nullable=False)
    drone_serial: str = Field(sa_column=Column(String(128), nullable=False))
    location: str = Field(sa_column=Column(String(255), nullable=False))
    duration_minutes: int = Field(nullable=False)
    max_temperature_c: float | None = Field(default=None)
    battery_consumption_pct: float | None = Field(default=None)
    outcome: OperationalOutcome = Field(sa_column=Column(SAEnum(OperationalOutcome), nullable=False))
    notes: str = Field(default="", nullable=False)
    telemetry_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class VerificationEvidence(TimestampMixin, SQLModel, table=True):
    __tablename__ = "verification_evidence"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    title: str = Field(sa_column=Column(String(255), nullable=False))
    evidence_type: VerificationEvidenceType = Field(sa_column=Column(SAEnum(VerificationEvidenceType), nullable=False))
    summary: str = Field(default="", nullable=False)
    observed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    source_name: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    source_reference: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))


class VerificationEvidenceLink(SQLModel, table=True):
    __tablename__ = "verification_evidence_links"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    verification_evidence_id: UUID = Field(foreign_key="verification_evidence.id", index=True)
    internal_object_type: FederatedInternalObjectType = Field(sa_column=Column(SAEnum(FederatedInternalObjectType), nullable=False))
    internal_object_id: UUID = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class Baseline(TimestampMixin, SQLModel, table=True):
    __tablename__ = "baselines"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    status: BaselineStatus = Field(default=BaselineStatus.draft, sa_column=Column(SAEnum(BaselineStatus), nullable=False))


class BaselineItem(SQLModel, table=True):
    __tablename__ = "baseline_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    baseline_id: UUID = Field(foreign_key="baselines.id", index=True)
    object_type: BaselineObjectType = Field(sa_column=Column(SAEnum(BaselineObjectType), nullable=False))
    object_id: UUID = Field(index=True)
    object_version: int = Field(nullable=False)


class Link(TimestampMixin, SQLModel, table=True):
    __tablename__ = "links"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    source_type: LinkObjectType = Field(sa_column=Column(SAEnum(LinkObjectType), nullable=False))
    source_id: UUID = Field(index=True)
    target_type: LinkObjectType = Field(sa_column=Column(SAEnum(LinkObjectType), nullable=False))
    target_id: UUID = Field(index=True)
    relation_type: RelationType = Field(sa_column=Column(SAEnum(RelationType), nullable=False))
    rationale: str | None = Field(default=None)


class SysMLRelation(SQLModel, table=True):
    __tablename__ = "sysml_relations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    source_type: SysMLObjectType = Field(sa_column=Column(SAEnum(SysMLObjectType), nullable=False))
    source_id: UUID = Field(index=True)
    target_type: SysMLObjectType = Field(sa_column=Column(SAEnum(SysMLObjectType), nullable=False))
    target_id: UUID = Field(index=True)
    relation_type: SysMLRelationType = Field(sa_column=Column(SAEnum(SysMLRelationType), nullable=False))
    rationale: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class RevisionSnapshot(SQLModel, table=True):
    __tablename__ = "revision_snapshots"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    object_type: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    object_id: UUID = Field(index=True)
    version: int = Field(nullable=False)
    snapshot_json: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    changed_at: datetime = Field(default_factory=utcnow, nullable=False)
    changed_by: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    change_summary: str | None = Field(default=None, sa_column=Column(String, nullable=True))


class ApprovalActionLog(SQLModel, table=True):
    __tablename__ = "approval_action_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    object_type: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    object_id: UUID = Field(index=True)
    from_status: str = Field(sa_column=Column(String(64), nullable=False))
    to_status: str = Field(sa_column=Column(String(64), nullable=False))
    action: str = Field(sa_column=Column(String(64), nullable=False))
    actor: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    comment: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class ChangeRequest(TimestampMixin, SQLModel, table=True):
    __tablename__ = "change_requests"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    status: ChangeRequestStatus = Field(default=ChangeRequestStatus.open, sa_column=Column(SAEnum(ChangeRequestStatus), nullable=False))
    severity: Severity = Field(sa_column=Column(SAEnum(Severity), nullable=False))


class ChangeImpact(SQLModel, table=True):
    __tablename__ = "change_impacts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    change_request_id: UUID = Field(foreign_key="change_requests.id", index=True)
    object_type: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    object_id: UUID = Field(index=True)
    impact_level: ImpactLevel = Field(sa_column=Column(SAEnum(ImpactLevel), nullable=False))
    notes: str = Field(default="", nullable=False)


class NonConformity(TimestampMixin, SQLModel, table=True):
    __tablename__ = "non_conformities"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: str = Field(default="", nullable=False)
    status: NonConformityStatus = Field(default=NonConformityStatus.detected, sa_column=Column(SAEnum(NonConformityStatus), nullable=False))
    severity: Severity = Field(sa_column=Column(SAEnum(Severity), nullable=False))


class ConnectorDefinition(TimestampMixin, SQLModel, table=True):
    __tablename__ = "connector_definitions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    name: str = Field(sa_column=Column(String(255), nullable=False))
    connector_type: ConnectorType = Field(sa_column=Column(SAEnum(ConnectorType), nullable=False))
    base_url: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    description: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    is_active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False))
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))


class ExternalArtifact(TimestampMixin, SQLModel, table=True):
    __tablename__ = "external_artifacts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    connector_definition_id: UUID | None = Field(default=None, foreign_key="connector_definitions.id", index=True)
    external_id: str = Field(sa_column=Column(String(128), index=True, nullable=False))
    artifact_type: ExternalArtifactType = Field(sa_column=Column(SAEnum(ExternalArtifactType), nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    canonical_uri: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    native_tool_url: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    status: ExternalArtifactStatus = Field(default=ExternalArtifactStatus.active, sa_column=Column(SAEnum(ExternalArtifactStatus), nullable=False))
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))


class ExternalArtifactVersion(SQLModel, table=True):
    __tablename__ = "external_artifact_versions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    external_artifact_id: UUID = Field(foreign_key="external_artifacts.id", index=True)
    version_label: str = Field(sa_column=Column(String(64), nullable=False))
    revision_label: str | None = Field(default=None, sa_column=Column(String(64), nullable=True))
    checksum_or_signature: str | None = Field(default=None, sa_column=Column(String(255), nullable=True))
    effective_date: dt_date | None = Field(default=None, nullable=True)
    source_timestamp: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class ArtifactLink(SQLModel, table=True):
    __tablename__ = "artifact_links"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    internal_object_type: FederatedInternalObjectType = Field(sa_column=Column(SAEnum(FederatedInternalObjectType), nullable=False))
    internal_object_id: UUID = Field(index=True)
    external_artifact_id: UUID = Field(foreign_key="external_artifacts.id", index=True)
    external_artifact_version_id: UUID | None = Field(default=None, foreign_key="external_artifact_versions.id", index=True)
    relation_type: ArtifactLinkRelationType = Field(sa_column=Column(SAEnum(ArtifactLinkRelationType), nullable=False))
    rationale: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class ConfigurationContext(TimestampMixin, SQLModel, table=True):
    __tablename__ = "configuration_contexts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(foreign_key="projects.id", index=True)
    key: str = Field(sa_column=Column(String(64), index=True, nullable=False))
    name: str = Field(sa_column=Column(String(255), nullable=False))
    description: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    context_type: ConfigurationContextType = Field(sa_column=Column(SAEnum(ConfigurationContextType), nullable=False))
    status: ConfigurationContextStatus = Field(default=ConfigurationContextStatus.draft, sa_column=Column(SAEnum(ConfigurationContextStatus), nullable=False))


class ConfigurationItemMapping(SQLModel, table=True):
    __tablename__ = "configuration_item_mappings"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    configuration_context_id: UUID = Field(foreign_key="configuration_contexts.id", index=True)
    item_kind: ConfigurationItemKind = Field(sa_column=Column(SAEnum(ConfigurationItemKind), nullable=False))
    internal_object_type: FederatedInternalObjectType | None = Field(default=None, sa_column=Column(SAEnum(FederatedInternalObjectType), nullable=True))
    internal_object_id: UUID | None = Field(default=None, index=True)
    internal_object_version: int | None = Field(default=None, nullable=True)
    external_artifact_version_id: UUID | None = Field(default=None, foreign_key="external_artifact_versions.id", index=True)
    role_label: str | None = Field(default=None, sa_column=Column(String(128), nullable=True))
    notes: str | None = Field(default=None, sa_column=Column(String, nullable=True))
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
