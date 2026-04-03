from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlmodel import Session

from app.models import *
from app.schemas import *

OBJECT_MODELS = {
    "project": Project,
    "requirement": Requirement,
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
    return _read(RequirementRead, _add(session, Requirement.model_validate(payload)))


def update_requirement(session: Session, obj_id: UUID, payload: RequirementUpdate) -> RequirementRead:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(RequirementRead, _add(session, item))


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


def create_test_case(session: Session, payload: TestCaseCreate) -> TestCaseRead:
    return _read(TestCaseRead, _add(session, TestCase.model_validate(payload)))


def update_test_case(session: Session, obj_id: UUID, payload: TestCaseUpdate) -> TestCaseRead:
    item = _get(session, TestCase, obj_id)
    if item is None:
        raise LookupError("Test case not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    _touch(item)
    return _read(TestCaseRead, _add(session, item))


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
    for object_type, model in ((BaselineObjectType.requirement, Requirement), (BaselineObjectType.component, Component), (BaselineObjectType.test_case, TestCase)):
        for row in _items(session.exec(select(model).where(model.project_id == payload.project_id))):
            obj = row[0] if not hasattr(row, "id") else row
            bi = _add(session, BaselineItem(baseline_id=baseline.id, object_type=object_type, object_id=obj.id, object_version=getattr(obj, "version", 1)))
            items.append(BaselineItemRead.model_validate(bi))
    return BaselineRead.model_validate(baseline), items


def list_baselines(session: Session, project_id: UUID) -> list[BaselineRead]:
    return [BaselineRead.model_validate(item) for item in _items(session.exec(select(Baseline).where(Baseline.project_id == project_id).order_by(desc(Baseline.created_at))))]


def get_baseline_detail(session: Session, baseline_id: UUID) -> dict[str, Any]:
    baseline = _get(session, Baseline, baseline_id)
    if baseline is None:
        raise LookupError("Baseline not found")
    items = [BaselineItemRead.model_validate(item) for item in session.exec(select(BaselineItem).where(BaselineItem.baseline_id == baseline_id))]
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
        stmt = stmt.where(((Link.source_type == object_type) & (Link.source_id == object_id)) | ((Link.target_type == object_type) & (Link.target_id == object_id)))
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
    links = list_links(session, project_id)
    direct_links = [l for l in links if (l.source_type.value == object_type and l.source_id == object_id) or (l.target_type.value == object_type and l.target_id == object_id)]
    direct: dict[tuple[str, UUID], ObjectSummary] = {}
    for link in direct_links:
        src = resolve_object(session, link.source_type.value, link.source_id)
        tgt = resolve_object(session, link.target_type.value, link.target_id)
        other = tgt if src["object_id"] == object_id else src
        direct[(other["object_type"], other["object_id"])] = summarize(other)
    secondary: dict[tuple[str, UUID], ObjectSummary] = {}
    for d in list(direct.values()):
        for link in links:
            if link.source_type.value == d.object_type and link.source_id == d.object_id:
                other = resolve_object(session, link.target_type.value, link.target_id)
                if other["object_id"] != object_id:
                    secondary[(other["object_type"], other["object_id"])] = summarize(other)
            if link.target_type.value == d.object_type and link.target_id == d.object_id:
                other = resolve_object(session, link.source_type.value, link.source_id)
                if other["object_id"] != object_id:
                    secondary[(other["object_type"], other["object_id"])] = summarize(other)
    likely = {**direct, **secondary}
    return ImpactResponse(project=project, object=summarize(root), direct=list(direct.values()), secondary=list(secondary.values()), likely_impacted=list(likely.values()), links=direct_links)


def get_requirement_detail(session: Session, obj_id: UUID) -> dict[str, Any]:
    item = _get(session, Requirement, obj_id)
    if item is None:
        raise LookupError("Requirement not found")
    return {"requirement": RequirementRead.model_validate(item), "links": list_links(session, item.project_id, "requirement", item.id), "impact": build_impact(session, item.project_id, "requirement", item.id)}


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
    return {"test_case": TestCaseRead.model_validate(item), "links": list_links(session, item.project_id, "test_case", item.id), "runs": runs, "impact": build_impact(session, item.project_id, "test_case", item.id)}


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
        {"project_id": project.id, "key": "DR-REQ-001", "title": "Drone shall fly for at least 30 minutes", "description": "Mission endurance target.", "category": RequirementCategory.performance, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-002", "title": "Drone shall stream real-time video to ground operator", "description": "Low latency live video stream.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-003", "title": "Drone shall operate between -5C and 40C", "description": "Environmental envelope.", "category": RequirementCategory.environment, "priority": Priority.high, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.approved, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-004", "title": "Drone shall detect obstacles during low altitude flight", "description": "Safety obstacle detection.", "category": RequirementCategory.safety, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-005", "title": "Drone shall support remote monitoring of battery and mission status", "description": "Telemetry requirement.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.demonstration, "status": RequirementStatus.approved, "version": 1},
    ]:
        item = _items(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == p["key"])))
        item = item[0] if item else None
        reqs[p["key"]] = item or _add(session, Requirement.model_validate(p))

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
