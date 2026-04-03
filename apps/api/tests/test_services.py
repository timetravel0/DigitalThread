from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Component, LinkObjectType, Project, Requirement
from app.schemas import ComponentCreate, LinkCreate, ProjectCreate, RequirementCreate
from app.models import ComponentType, Priority, RelationType, RequirementCategory, VerificationMethod
from app.services import build_impact, build_matrix, create_component, create_link, create_project, create_requirement, get_project_dashboard, seed_demo


def make_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_seed_demo_populates_kpis():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        dashboard = get_project_dashboard(session, project.id)

        assert dashboard.kpis.total_requirements == 5
        assert dashboard.kpis.requirements_with_allocated_components == 5
        assert dashboard.kpis.requirements_with_verifying_tests == 4
        assert dashboard.kpis.requirements_at_risk == 1
        assert dashboard.kpis.failed_tests_last_30_days == 1
        assert dashboard.kpis.open_change_requests == 1


def test_link_validation_rejects_cross_project():
    with make_session() as session:
        p1 = create_project(session, ProjectCreate(code="P1", name="P1", description=""))
        p2 = create_project(session, ProjectCreate(code="P2", name="P2", description=""))
        req = create_requirement(
            session,
            RequirementCreate(
                project_id=p1.id,
                key="R1",
                title="Requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        cmp = create_component(
            session,
            ComponentCreate(project_id=p2.id, key="C1", name="Component", type=ComponentType.other),
        )

        try:
            create_link(
                session,
                LinkCreate(
                    project_id=p1.id,
                    source_type=LinkObjectType.requirement,
                    source_id=req.id,
                    target_type=LinkObjectType.component,
                    target_id=cmp.id,
                    relation_type=RelationType.allocated_to,
                ),
            )
            assert False, "Expected cross-project link validation to fail"
        except ValueError:
            pass


def test_matrix_and_impact_use_seeded_links():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        matrix = build_matrix(session, project.id, mode="components")
        impact = build_impact(session, project.id, "requirement", session.exec(select(Requirement).where(Requirement.key == "DR-REQ-001")).one().id)

        assert matrix.rows
        assert matrix.columns
        assert any(cell.linked for cell in matrix.cells)
        assert any(item.object_type == "component" for item in impact.direct)
        assert any(item.object_type == "component" for item in impact.likely_impacted)

