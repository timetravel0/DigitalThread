from __future__ import annotations

from datetime import date as dt_date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum as SAEnum, JSON, String
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
    approved = "approved"
    implemented = "implemented"
    verified = "verified"
    failed = "failed"
    retired = "retired"


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
    ready = "ready"
    executed = "executed"
    failed = "failed"
    passed = "passed"
    archived = "archived"


class TestRunResult(str, Enum):
    passed = "passed"
    failed = "failed"
    partial = "partial"


class OperationalOutcome(str, Enum):
    success = "success"
    degraded = "degraded"
    failure = "failure"


class BaselineStatus(str, Enum):
    draft = "draft"
    released = "released"
    obsolete = "obsolete"


class BaselineObjectType(str, Enum):
    requirement = "requirement"
    component = "component"
    test_case = "test_case"


class LinkObjectType(str, Enum):
    requirement = "requirement"
    component = "component"
    test_case = "test_case"
    test_run = "test_run"
    operational_run = "operational_run"
    change_request = "change_request"


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


class ChangeRequestStatus(str, Enum):
    open = "open"
    analysis = "analysis"
    approved = "approved"
    rejected = "rejected"
    implemented = "implemented"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ImpactLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


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
