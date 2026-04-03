from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.core import get_settings
from app.db import get_session, init_db
from app.schemas import *
from app.services import *

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def db(session: Session = Depends(get_session)) -> Session:
    return session


def api_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/projects", response_model=list[ProjectRead])
def list_projects_endpoint(session: Session = Depends(db)):
    return list_projects_service(session)


@app.post("/api/projects", response_model=ProjectRead, status_code=201)
def create_project_endpoint(payload: ProjectCreate, session: Session = Depends(db)):
    try:
        return create_project(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}", response_model=ProjectRead)
def get_project_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        return get_project_service(session, project_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/projects/{project_id}", response_model=ProjectRead)
def update_project_endpoint(project_id: UUID, payload: ProjectUpdate, session: Session = Depends(db)):
    try:
        return update_project(session, project_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/dashboard", response_model=GlobalDashboard)
def dashboard_endpoint(session: Session = Depends(db)):
    return get_global_dashboard(session)


@app.get("/api/projects/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        return get_project_dashboard(session, project_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements", response_model=list[RequirementRead])
def list_requirements_endpoint(
    project_id: UUID = Query(...),
    status: RequirementStatus | None = None,
    category: RequirementCategory | None = None,
    priority: Priority | None = None,
    session: Session = Depends(db),
):
    return list_requirements(session, project_id, status=status, category=category, priority=priority)


@app.post("/api/requirements", response_model=RequirementRead, status_code=201)
def create_requirement_endpoint(payload: RequirementCreate, session: Session = Depends(db)):
    try:
        return create_requirement(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements/{obj_id}")
def requirement_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_requirement_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/requirements/{obj_id}", response_model=RequirementRead)
def update_requirement_endpoint(obj_id: UUID, payload: RequirementUpdate, session: Session = Depends(db)):
    try:
        return update_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/components", response_model=list[ComponentRead])
def list_components_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_components(session, project_id)


@app.post("/api/components", response_model=ComponentRead, status_code=201)
def create_component_endpoint(payload: ComponentCreate, session: Session = Depends(db)):
    try:
        return create_component(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/components/{obj_id}")
def component_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_component_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/components/{obj_id}", response_model=ComponentRead)
def update_component_endpoint(obj_id: UUID, payload: ComponentUpdate, session: Session = Depends(db)):
    try:
        return update_component(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases", response_model=list[TestCaseRead])
def list_test_cases_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_test_cases(session, project_id)


@app.post("/api/test-cases", response_model=TestCaseRead, status_code=201)
def create_test_case_endpoint(payload: TestCaseCreate, session: Session = Depends(db)):
    try:
        return create_test_case(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases/{obj_id}")
def test_case_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_test_case_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/test-cases/{obj_id}", response_model=TestCaseRead)
def update_test_case_endpoint(obj_id: UUID, payload: TestCaseUpdate, session: Session = Depends(db)):
    try:
        return update_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-runs", response_model=list[TestRunRead])
def list_test_runs_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_test_runs(session, project_id)


@app.post("/api/test-runs", response_model=TestRunRead, status_code=201)
def create_test_run_endpoint(payload: TestRunCreate, session: Session = Depends(db)):
    try:
        return create_test_run(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/operational-runs", response_model=list[OperationalRunRead])
def list_operational_runs_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_operational_runs(session, project_id)


@app.post("/api/operational-runs", response_model=OperationalRunRead, status_code=201)
def create_operational_run_endpoint(payload: OperationalRunCreate, session: Session = Depends(db)):
    try:
        return create_operational_run(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/operational-runs/{obj_id}", response_model=OperationalRunRead)
def update_operational_run_endpoint(obj_id: UUID, payload: OperationalRunUpdate, session: Session = Depends(db)):
    try:
        return update_operational_run(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines", response_model=list[BaselineRead])
def list_baselines_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_baselines(session, project_id)


@app.post("/api/baselines", status_code=201)
def create_baseline_endpoint(payload: BaselineCreate, session: Session = Depends(db)):
    try:
        baseline, items = create_baseline(session, payload)
        return {"baseline": baseline, "items": items}
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/baselines/{obj_id}")
def baseline_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_baseline_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-requests", response_model=list[ChangeRequestRead])
def list_change_requests_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_change_requests(session, project_id)


@app.post("/api/change-requests", response_model=ChangeRequestRead, status_code=201)
def create_change_request_endpoint(payload: ChangeRequestCreate, session: Session = Depends(db)):
    try:
        return create_change_request(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-requests/{obj_id}")
def change_request_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_change_request_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.put("/api/change-requests/{obj_id}", response_model=ChangeRequestRead)
def update_change_request_endpoint(obj_id: UUID, payload: ChangeRequestUpdate, session: Session = Depends(db)):
    try:
        return update_change_request(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/change-impacts", response_model=list[ChangeImpactRead])
def list_change_impacts_endpoint(change_request_id: UUID = Query(...), session: Session = Depends(db)):
    return list_change_impacts(session, change_request_id)


@app.post("/api/change-impacts", response_model=ChangeImpactRead, status_code=201)
def create_change_impact_endpoint(payload: ChangeImpactCreate, session: Session = Depends(db)):
    try:
        return create_change_impact(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/links", response_model=list[LinkRead])
def list_links_endpoint(project_id: UUID = Query(...), object_type: str | None = None, object_id: UUID | None = None, session: Session = Depends(db)):
    return list_links(session, project_id, object_type=object_type, object_id=object_id)


@app.post("/api/links", response_model=LinkRead, status_code=201)
def create_link_endpoint(payload: LinkCreate, session: Session = Depends(db)):
    try:
        return create_link(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/matrix", response_model=MatrixResponse)
def matrix_endpoint(project_id: UUID, mode: str = Query("components"), status: RequirementStatus | None = None, category: RequirementCategory | None = None, session: Session = Depends(db)):
    return build_matrix(session, project_id, mode=mode, status=status, category=category)


@app.get("/api/projects/{project_id}/impact/{object_type}/{object_id}", response_model=ImpactResponse)
def impact_endpoint(project_id: UUID, object_type: str, object_id: UUID, session: Session = Depends(db)):
    return build_impact(session, project_id, object_type, object_id)


@app.post("/api/seed/demo")
def seed_demo_endpoint(session: Session = Depends(db)):
    try:
        return seed_demo(session)
    except Exception as exc:
        raise api_error(exc)
