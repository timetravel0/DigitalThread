"""Impact service layer for the DigitalThread API."""

from collections import defaultdict, deque
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlmodel import Session

from app.models import (
    ArtifactLink,
    Baseline,
    BaselineItem,
    BlockContainment,
    ChangeImpact,
    ChangeRequest,
    ChangeRequestStatus,
    Component,
    Link,
    LinkObjectType,
    OperationalEvidence,
    OperationalEvidenceLink,
    OperationalOutcome,
    Project,
    RelationType,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    RequirementVerificationStatus,
    SimulationEvidence,
    SimulationEvidenceLink,
    SimulationEvidenceLinkObjectType,
    SysMLRelation,
    TestCase,
    TestRun,
    TestRunResult,
    VerificationEvidence,
    VerificationEvidenceLink,
)
from app.schemas import (
    ChangeImpactRead,
    ChangeRequestRead,
    ComponentRead,
    DashboardKpis,
    GlobalDashboard,
    ImpactResponse,
    LinkRead,
    MatrixCell,
    MatrixColumn,
    MatrixResponse,
    MatrixRow,
    ProjectDashboard,
    RequirementRead,
    RequirementVerificationEvaluation,
    RequirementVerificationStatus,
    TestCaseRead,
    TestRunRead,
    VerificationStatusBreakdown,
)
from app.services._common import (
    _evaluate_requirement_verification,
    _impact_context_internal_ids,
    _impact_node_key,
    _items,
    _latest_test_run,
    _operational_evidence_signal_from_record,
    _status_value,
    _utc_datetime,
    _verification_signal_from_evidence,
    _verification_status_breakdown,
)
from app.services.change_request_service import list_change_impacts, list_change_request_history
from app.services.configuration_service import list_configuration_item_mappings
from app.services.federation_service import list_artifact_links
from app.services.link_service import list_links, list_sysml_relations
from app.services.test_service import list_test_case_history, list_test_cases
from app.services.component_service import list_components
from app.services.requirement_service import list_requirements

def get_global_dashboard(session: Session) -> GlobalDashboard:
    from app.services.project_service import list_projects_service

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


def get_project_dashboard(session: Session, project_id: UUID) -> ProjectDashboard:
    from app.services.change_request_service import list_change_requests
    from app.services.project_service import get_project_service
    from app.services.test_service import list_test_runs

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

def build_matrix(session: Session, project_id: UUID, mode: str, status: RequirementStatus | None = None, category: RequirementCategory | None = None) -> MatrixResponse:
    from app.services.project_service import get_project_service

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
    from app.services.project_service import get_project_service
    from app.services.registry_service import resolve_object, summarize
    from app.services.block_service import list_block_containments

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
    from app.services.evidence_service import list_operational_evidence, list_simulation_evidence, list_verification_evidence

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
    from app.services.evidence_service import list_verification_evidence

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
    from app.services.evidence_service import list_simulation_evidence, list_verification_evidence

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
