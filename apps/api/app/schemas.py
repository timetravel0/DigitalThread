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


class RequirementCreate(BaseModel):
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


class RequirementRead(RequirementCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


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


class TestCaseCreate(BaseModel):
    project_id: UUID
    key: str
    title: str
    description: str = ""
    method: TestMethod
    status: TestCaseStatus = TestCaseStatus.draft
    version: int = 1


class TestCaseUpdate(BaseModel):
    project_id: UUID | None = None
    key: str | None = None
    title: str | None = None
    description: str | None = None
    method: TestMethod | None = None
    status: TestCaseStatus | None = None
    version: int | None = None


class TestCaseRead(TestCaseCreate, ORMBase):
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


class BaselineCreate(BaseModel):
    project_id: UUID
    name: str
    description: str = ""
    status: BaselineStatus = BaselineStatus.draft


class BaselineRead(BaselineCreate, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


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


class ChangeImpactCreate(BaseModel):
    change_request_id: UUID
    object_type: str
    object_id: UUID
    impact_level: ImpactLevel
    notes: str = ""


class ChangeImpactRead(ChangeImpactCreate, ORMBase):
    id: UUID


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
    recent_test_runs: list[TestRunRead]
    recent_changes: list[ChangeRequestRead]
    recent_links: list[LinkRead]


class GlobalDashboard(BaseModel):
    projects: list[ProjectRead]
    kpis: DashboardKpis
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
