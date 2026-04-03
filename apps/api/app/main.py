from __future__ import annotations

import json
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
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
@app.patch("/api/projects/{project_id}", response_model=ProjectRead)
def update_project_endpoint(project_id: UUID, payload: ProjectUpdate, session: Session = Depends(db)):
    try:
        return update_project(session, project_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/projects/{project_id}/export")
def export_project_endpoint(project_id: UUID, session: Session = Depends(db)):
    try:
        bundle = export_project_bundle(session, project_id)
        filename = f"threadlite-{bundle['project']['code']}.json"
        return Response(
            content=json.dumps(bundle, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
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


@app.get("/api/requirements/{obj_id}", response_model=dict)
def requirement_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_requirement_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/requirements/{obj_id}", response_model=RequirementRead)
def patch_requirement_endpoint(obj_id: UUID, payload: RequirementUpdate, session: Session = Depends(db)):
    try:
        return update_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/submit-review", response_model=RequirementRead)
def submit_requirement_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_requirement_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/approve", response_model=RequirementRead)
def approve_requirement_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/reject", response_model=RequirementRead)
def reject_requirement_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_requirement(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/send-draft", response_model=RequirementRead)
def requirement_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_requirement_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/requirements/{obj_id}/create-draft-version", response_model=RequirementRead)
def requirement_create_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_requirement_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/requirements/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def requirement_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_requirement_history(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks", response_model=list[BlockRead])
def list_blocks_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_blocks(session, project_id)


@app.post("/api/blocks", response_model=BlockRead, status_code=201)
def create_block_endpoint(payload: BlockCreate, session: Session = Depends(db)):
    try:
        return create_block(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks/{obj_id}", response_model=dict)
def block_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_block_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/blocks/{obj_id}", response_model=BlockRead)
def patch_block_endpoint(obj_id: UUID, payload: BlockUpdate, session: Session = Depends(db)):
    try:
        return update_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/submit-review", response_model=BlockRead)
def submit_block_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_block_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/approve", response_model=BlockRead)
def approve_block_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/reject", response_model=BlockRead)
def reject_block_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_block(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/send-draft", response_model=BlockRead)
def block_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_block_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/blocks/{obj_id}/create-draft-version", response_model=BlockRead)
def block_create_draft_version_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_block_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/blocks/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def block_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_block_history(session, obj_id)
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


@app.get("/api/test-cases/{obj_id}", response_model=dict)
def test_case_detail_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return get_test_case_detail(session, obj_id)
    except Exception as exc:
        raise api_error(exc)


@app.patch("/api/test-cases/{obj_id}", response_model=TestCaseRead)
def patch_test_case_endpoint(obj_id: UUID, payload: TestCaseUpdate, session: Session = Depends(db)):
    try:
        return update_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/submit-review", response_model=TestCaseRead)
def submit_test_case_review_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return submit_test_case_for_review(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/approve", response_model=TestCaseRead)
def approve_test_case_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return approve_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/reject", response_model=TestCaseRead)
def reject_test_case_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return reject_test_case(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/send-draft", response_model=TestCaseRead)
def test_case_send_draft_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return send_test_case_back_to_draft(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.post("/api/test-cases/{obj_id}/create-draft-version", response_model=TestCaseRead)
def test_case_create_draft_version_endpoint(obj_id: UUID, payload: WorkflowActionPayload | None = None, session: Session = Depends(db)):
    try:
        return create_test_case_draft_version(session, obj_id, payload)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/test-cases/{obj_id}/history", response_model=list[RevisionSnapshotRead])
def test_case_history_endpoint(obj_id: UUID, session: Session = Depends(db)):
    try:
        return list_test_case_history(session, obj_id)
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


@app.patch("/api/operational-runs/{obj_id}", response_model=OperationalRunRead)
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


@app.patch("/api/change-requests/{obj_id}", response_model=ChangeRequestRead)
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


@app.get("/api/sysml-relations", response_model=list[SysMLRelationRead])
def list_sysml_relations_endpoint(project_id: UUID = Query(...), object_type: str | None = None, object_id: UUID | None = None, session: Session = Depends(db)):
    return list_sysml_relations(session, project_id, object_type=object_type, object_id=object_id)


@app.post("/api/sysml-relations", response_model=SysMLRelationRead, status_code=201)
def create_sysml_relation_endpoint(payload: SysMLRelationCreate, session: Session = Depends(db)):
    try:
        return create_sysml_relation(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/sysml-relations/{relation_id}", status_code=204)
def delete_sysml_relation_endpoint(relation_id: UUID, session: Session = Depends(db)):
    try:
        delete_sysml_relation(session, relation_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/block-containments", response_model=list[BlockContainmentRead])
def list_block_containments_endpoint(project_id: UUID = Query(...), object_id: UUID | None = None, session: Session = Depends(db)):
    return list_block_containments(session, project_id, obj_id=object_id)


@app.post("/api/block-containments", response_model=BlockContainmentRead, status_code=201)
def create_block_containment_endpoint(payload: BlockContainmentCreate, session: Session = Depends(db)):
    try:
        return create_block_containment(session, payload)
    except Exception as exc:
        raise api_error(exc)


@app.delete("/api/block-containments/{containment_id}", status_code=204)
def delete_block_containment_endpoint(containment_id: UUID, session: Session = Depends(db)):
    try:
        delete_block_containment(session, containment_id)
    except Exception as exc:
        raise api_error(exc)


@app.get("/api/review-queue", response_model=ReviewQueueResponse)
def review_queue_endpoint(project_id: UUID = Query(...), session: Session = Depends(db)):
    return list_review_queue(session, project_id)


@app.get("/api/projects/{project_id}/sysml/block-tree", response_model=SysMLTreeResponse)
def block_tree_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_block_tree(session, project_id)


@app.get("/api/projects/{project_id}/sysml/satisfaction", response_model=SysMLSatisfactionResponse)
def satisfaction_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_satisfaction_view(session, project_id)


@app.get("/api/projects/{project_id}/sysml/verification", response_model=SysMLVerificationResponse)
def verification_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_verification_view(session, project_id)


@app.get("/api/projects/{project_id}/sysml/derivations", response_model=SysMLDerivationResponse)
def derivations_endpoint(project_id: UUID, session: Session = Depends(db)):
    return build_derivation_view(session, project_id)


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
