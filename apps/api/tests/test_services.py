import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Block,
    BlockStatus,
    Component,
    ComponentType,
    Link,
    LinkObjectType,
    Priority,
    Project,
    RelationType,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    SysMLObjectType,
    SysMLRelation,
    SysMLRelationType,
    TestCase,
    TestCaseStatus,
    VerificationMethod,
)
from app.schemas import (
    BlockCreate,
    BaselineCreate,
    LinkCreate,
    ProjectCreate,
    RequirementCreate,
    SysMLRelationCreate,
    TestCaseCreate,
    WorkflowActionPayload,
)
from app.models import BlockKind, AbstractionLevel, TestMethod
from app.services import (
    approve_requirement,
    build_impact,
    create_baseline,
    create_block,
    create_link,
    create_project,
    create_requirement,
    create_requirement_draft_version,
    create_sysml_relation,
    create_test_case,
    export_project_bundle,
    get_project_dashboard,
    list_requirement_history,
    reject_requirement,
    seed_demo,
    submit_requirement_for_review,
)


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_seed_demo_populates_sysml_driven_kpis():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        dashboard = get_project_dashboard(session, project.id)

        assert dashboard.kpis.total_requirements == 6
        assert dashboard.kpis.requirements_with_allocated_components == 5
        assert dashboard.kpis.requirements_with_verifying_tests == 4
        assert dashboard.kpis.requirements_at_risk == 1
        assert dashboard.kpis.failed_tests_last_30_days == 1
        assert dashboard.kpis.open_change_requests == 1


def test_requirement_approval_workflow_and_draft_version():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P1", name="P1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-1",
                title="Requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )

        with pytest.raises(ValueError):
            approve_requirement(session, requirement.id)

        submitted = submit_requirement_for_review(session, requirement.id, WorkflowActionPayload(actor="reviewer"))
        approved = approve_requirement(session, submitted.id, WorkflowActionPayload(actor="approver"))
        draft = create_requirement_draft_version(session, approved.id, WorkflowActionPayload(change_summary="Refine text"))

        assert approved.status == RequirementStatus.approved
        assert draft.version == approved.version + 1
        assert draft.status == RequirementStatus.draft
        assert len(list_requirement_history(session, approved.id)) >= 3


def test_sysml_relation_validation_and_baseline_filters_non_approved_items():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P2", name="P2", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-APPROVED",
                title="Approved requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        draft_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-DRAFT",
                title="Draft requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-1",
                name="Block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-1",
                title="Test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )

        relation = create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.block,
                source_id=block.id,
                target_type=SysMLObjectType.requirement,
                target_id=requirement.id,
                relation_type=SysMLRelationType.satisfy,
            ),
        )
        assert relation.relation_type == SysMLRelationType.satisfy

        with pytest.raises(ValueError):
            create_sysml_relation(
                session,
                SysMLRelationCreate(
                    project_id=project.id,
                    source_type=SysMLObjectType.block,
                    source_id=block.id,
                    target_type=SysMLObjectType.requirement,
                    target_id=requirement.id,
                    relation_type=SysMLRelationType.verify,
                ),
            )

        baseline, items = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Baseline",
                description="Filtered baseline",
                requirement_ids=[requirement.id, draft_requirement.id],
            ),
        )

        assert baseline.name == "Baseline"
        assert any(item.object_id == requirement.id for item in items)
        assert all(item.object_id != draft_requirement.id for item in items)


def test_impact_analysis_includes_blocks_and_tests_from_sysml_relations():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        req = session.exec(select(Requirement).where(Requirement.key == "DR-REQ-001")).one()
        impact = build_impact(session, project.id, "requirement", req.id)

        assert any(item.object_type == "block" for item in impact.direct)
        assert any(item.object_type == "test_case" for item in impact.secondary + impact.direct)
        assert impact.related_baselines


def test_project_export_bundle_contains_full_project_payload():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        bundle = export_project_bundle(session, project.id)

        assert bundle["schema"] == "threadlite.project.export.v1"
        assert bundle["project"]["code"] == "DRONE-001"
        assert len(bundle["requirements"]) >= 6
        assert len(bundle["blocks"]) >= 7
        assert len(bundle["sysml_relations"]) >= 8
        assert bundle["baselines"]
        assert bundle["revision_snapshots"]
