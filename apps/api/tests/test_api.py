from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.main import app
from app.db import get_session
import app.main as app_main
from app.models import (
    AbstractionLevel,
    BaselineStatus,
    BlockKind,
    BlockContainmentRelationType,
    ChangeRequestStatus,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConnectorType,
    ArtifactLinkRelationType,
    ExternalArtifactType,
    FederatedInternalObjectType,
    LinkObjectType,
    RelationType,
    Priority,
    RequirementCategory,
    RequirementStatus,
    SimulationEvidenceResult,
    OperationalEvidenceQualityStatus,
    OperationalEvidenceSourceType,
    OperationalOutcome,
    TestCaseStatus,
    TestMethod,
    VerificationMethod,
    VerificationEvidenceType,
    SysMLObjectType,
    SysMLRelationType,
)


@pytest.fixture(scope="function")
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(app_main, "init_db", lambda: None)
    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_projects_starts_empty(client: TestClient):
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json() == []


def test_create_project_endpoint(client: TestClient):
    payload = {"code": "PRJ-001", "name": "Demo Project", "description": "Demo"}
    response = client.post("/api/projects", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["code"] == payload["code"]


def test_get_project_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-002", "name": "Project Two", "description": "Demo"}).json()

    ok_response = client.get(f"/api/projects/{created['id']}")
    assert ok_response.status_code == 200
    assert ok_response.json()["id"] == created["id"]

    missing_response = client.get(f"/api/projects/{uuid4()}")
    assert missing_response.status_code == 404


def test_update_project_put_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-003", "name": "Project Three", "description": "Demo"}).json()

    response = client.put(
        f"/api/projects/{created['id']}",
        json={"name": "Project Three Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Project Three Updated"


def test_update_project_patch_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-004", "name": "Project Four", "description": "Demo"}).json()

    response = client.patch(
        f"/api/projects/{created['id']}",
        json={"description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"


def test_project_dashboard_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-005", "name": "Project Five", "description": "Demo"}).json()

    response = client.get(f"/api/projects/{created['id']}/dashboard")
    assert response.status_code == 200
    assert "kpis" in response.json()


def test_project_tab_stats_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-006", "name": "Project Six", "description": "Demo"}).json()

    response = client.get(f"/api/projects/{created['id']}/tab-stats")
    assert response.status_code == 200
    assert "requirements" in response.json()


def test_global_dashboard_endpoint(client: TestClient):
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert "projects" in response.json()


def test_authoritative_registry_summary_endpoint(client: TestClient):
    created = client.post("/api/projects", json={"code": "PRJ-007", "name": "Project Seven", "description": "Demo"}).json()

    response = client.get(f"/api/projects/{created['id']}/authoritative-registry-summary")
    assert response.status_code == 200
    body = response.json()
    assert "revision_snapshot_integrity_status" in body


def test_requirements_workflow_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "REQ-PRJ", "name": "Requirements Project", "description": "Demo"}).json()

    create_response = client.post(
        "/api/requirements",
        json={
            "project_id": project["id"],
            "key": "REQ-001",
            "title": "First requirement",
            "category": RequirementCategory.performance.value,
            "priority": Priority.high.value,
            "verification_method": VerificationMethod.test.value,
        },
    )
    assert create_response.status_code == 201
    requirement = create_response.json()

    list_response = client.get("/api/requirements", params={"project_id": project["id"]})
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert list_response.json()

    detail_response = client.get(f"/api/requirements/{requirement['id']}")
    assert detail_response.status_code == 200
    assert "verification_evaluation" in detail_response.json()

    patch_response = client.patch(f"/api/requirements/{requirement['id']}", json={"title": "Updated requirement"})
    assert patch_response.status_code == 200
    assert patch_response.json()["title"] == "Updated requirement"

    submit_response = client.post(f"/api/requirements/{requirement['id']}/submit-review")
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == RequirementStatus.in_review.value

    approve_response = client.post(f"/api/requirements/{requirement['id']}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == RequirementStatus.approved.value

    rejected_response = client.post(f"/api/requirements/{requirement['id']}/reject")
    assert rejected_response.status_code == 400

    draft_response = client.post(f"/api/requirements/{requirement['id']}/create-draft-version")
    assert draft_response.status_code == 200
    assert draft_response.json()["status"] == RequirementStatus.draft.value

    history_response = client.get(f"/api/requirements/{requirement['id']}/history")
    assert history_response.status_code == 200
    assert isinstance(history_response.json(), list)

    queue_response = client.get("/api/review-queue", params={"project_id": project["id"]})
    assert queue_response.status_code == 200


def test_blocks_workflow_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "BLK-PRJ", "name": "Blocks Project", "description": "Demo"}).json()

    create_response = client.post(
        "/api/blocks",
        json={
            "project_id": project["id"],
            "key": "BLK-001",
            "name": "Main Assembly",
            "block_kind": BlockKind.system.value,
            "abstraction_level": AbstractionLevel.logical.value,
        },
    )
    assert create_response.status_code == 201
    block = create_response.json()

    list_response = client.get("/api/blocks", params={"project_id": project["id"]})
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert list_response.json()

    submit_response = client.post(f"/api/blocks/{block['id']}/submit-review")
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "in_review"

    approve_response = client.post(f"/api/blocks/{block['id']}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    draft_response = client.post(f"/api/blocks/{block['id']}/create-draft-version")
    assert draft_response.status_code == 200
    assert draft_response.json()["status"] == "draft"


def test_test_cases_workflow_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "TST-PRJ", "name": "Tests Project", "description": "Demo"}).json()

    create_response = client.post(
        "/api/test-cases",
        json={
            "project_id": project["id"],
            "key": "TST-001",
            "title": "Check main flow",
                "method": TestMethod.simulation.value,
            "status": TestCaseStatus.draft.value,
        },
    )
    assert create_response.status_code == 201
    test_case = create_response.json()

    list_response = client.get("/api/test-cases", params={"project_id": project["id"]})
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)
    assert list_response.json()

    submit_response = client.post(f"/api/test-cases/{test_case['id']}/submit-review")
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == TestCaseStatus.in_review.value

    approve_response = client.post(f"/api/test-cases/{test_case['id']}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == TestCaseStatus.approved.value


def test_baselines_change_requests_and_configuration_contexts_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "CFG-PRJ", "name": "Config Project", "description": "Demo"}).json()

    requirement = client.post(
        "/api/requirements",
        json={
            "project_id": project["id"],
            "key": "REQ-BAS-001",
            "title": "Approved requirement",
            "category": RequirementCategory.performance.value,
            "priority": Priority.high.value,
            "verification_method": VerificationMethod.test.value,
        },
    ).json()
    client.post(f"/api/requirements/{requirement['id']}/submit-review")
    client.post(f"/api/requirements/{requirement['id']}/approve")

    baseline_create = client.post(
        "/api/baselines",
        json={
            "project_id": project["id"],
            "name": "Baseline A",
            "description": "First baseline",
            "status": BaselineStatus.draft.value,
            "requirement_ids": [requirement["id"]],
            "block_ids": [],
            "test_case_ids": [],
            "include_unapproved": False,
        },
    )
    assert baseline_create.status_code == 201
    baseline_payload = baseline_create.json()
    baseline = baseline_payload["baseline"]

    list_baselines = client.get("/api/baselines", params={"project_id": project["id"]})
    assert list_baselines.status_code == 200

    baseline_detail = client.get(f"/api/baselines/{baseline['id']}")
    assert baseline_detail.status_code == 200
    assert baseline_detail.json()["baseline"]["release_flag"] in {True, False}

    release_response = client.post(f"/api/baselines/{baseline['id']}/release")
    assert release_response.status_code == 200
    assert release_response.json()["status"] == BaselineStatus.released.value

    obsolete_response = client.post(f"/api/baselines/{baseline['id']}/obsolete")
    assert obsolete_response.status_code == 200
    assert obsolete_response.json()["status"] == BaselineStatus.obsolete.value

    bridge_context = client.get(f"/api/baselines/{baseline['id']}/bridge-context")
    assert bridge_context.status_code == 200

    second_baseline = client.post(
        "/api/baselines",
        json={
            "project_id": project["id"],
            "name": "Baseline B",
            "description": "Second baseline",
            "status": BaselineStatus.draft.value,
            "requirement_ids": [requirement["id"]],
            "block_ids": [],
            "test_case_ids": [],
            "include_unapproved": False,
        },
    ).json()
    comparison = client.get(f"/api/baselines/{baseline['id']}/compare-baseline/{second_baseline['baseline']['id']}")
    assert comparison.status_code == 200
    assert "summary" in comparison.json()

    cr_create = client.post(
        "/api/change-requests",
        json={
            "project_id": project["id"],
            "key": "CR-001",
            "title": "Initial change request",
            "description": "Demo",
            "status": ChangeRequestStatus.open.value,
            "severity": "medium",
        },
    )
    assert cr_create.status_code == 201
    change_request = cr_create.json()

    list_crs = client.get("/api/change-requests", params={"project_id": project["id"]})
    assert list_crs.status_code == 200

    cr_detail = client.get(f"/api/change-requests/{change_request['id']}")
    assert cr_detail.status_code == 200
    assert "history" in cr_detail.json()

    bad_cr = client.post(
        "/api/change-requests",
        json={
            "project_id": project["id"],
            "key": "CR-002",
            "title": "Invalid state change request",
            "description": "Demo",
            "status": ChangeRequestStatus.analysis.value,
            "severity": "medium",
        },
    )
    assert bad_cr.status_code == 400

    submit_analysis = client.post(f"/api/change-requests/{change_request['id']}/submit-analysis", json={})
    assert submit_analysis.status_code == 200

    approve_cr = client.post(f"/api/change-requests/{change_request['id']}/approve", json={})
    assert approve_cr.status_code == 200

    implement_cr = client.post(f"/api/change-requests/{change_request['id']}/implement", json={})
    assert implement_cr.status_code == 200

    close_cr = client.post(f"/api/change-requests/{change_request['id']}/close", json={})
    assert close_cr.status_code == 200
    assert close_cr.json()["status"] == ChangeRequestStatus.closed.value

    context_create = client.post(
        f"/api/projects/{project['id']}/configuration-contexts",
        json={
            "project_id": project["id"],
            "key": "CTX-001",
            "name": "Working context",
            "description": "Demo",
            "context_type": ConfigurationContextType.working.value,
            "status": ConfigurationContextStatus.draft.value,
        },
    )
    assert context_create.status_code == 201
    context = context_create.json()

    list_contexts = client.get(f"/api/projects/{project['id']}/configuration-contexts")
    assert list_contexts.status_code == 200

    context_detail = client.get(f"/api/configuration-contexts/{context['id']}")
    assert context_detail.status_code == 200
    assert "resolved_view" in context_detail.json()

    req_mapping = client.post(
        f"/api/configuration-contexts/{context['id']}/items",
        json={
            "item_kind": ConfigurationItemKind.internal_requirement.value,
            "internal_object_type": "requirement",
            "internal_object_id": requirement["id"],
            "internal_object_version": requirement["version"],
            "role_label": "anchor",
            "notes": "Included requirement",
        },
    )
    assert req_mapping.status_code == 201
    mapping = req_mapping.json()

    list_mappings = client.get(f"/api/configuration-contexts/{context['id']}/items")
    assert list_mappings.status_code == 200

    delete_mapping = client.delete(f"/api/configuration-item-mappings/{mapping['id']}")
    assert delete_mapping.status_code == 204

    frozen_context = client.patch(
        f"/api/configuration-contexts/{context['id']}",
        json={"status": ConfigurationContextStatus.frozen.value},
    )
    assert frozen_context.status_code == 200

    blocked_update = client.patch(
        f"/api/configuration-contexts/{context['id']}",
        json={"name": "Changed after freeze"},
    )
    assert blocked_update.status_code == 400


def test_evidence_operational_runs_test_runs_and_import_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "EVD-PRJ", "name": "Evidence Project", "description": "Demo"}).json()

    requirement = client.post(
        "/api/requirements",
        json={
            "project_id": project["id"],
            "key": "REQ-EVD-001",
            "title": "Evidence-linked requirement",
            "category": RequirementCategory.performance.value,
            "priority": Priority.high.value,
            "verification_method": VerificationMethod.test.value,
        },
    ).json()
    client.post(f"/api/requirements/{requirement['id']}/submit-review")
    client.post(f"/api/requirements/{requirement['id']}/approve")

    test_case = client.post(
        "/api/test-cases",
        json={
            "project_id": project["id"],
            "key": "TST-EVD-001",
            "title": "Evidence test case",
            "method": TestMethod.simulation.value,
            "status": TestCaseStatus.draft.value,
        },
    ).json()

    verification_create = client.post(
        f"/api/projects/{project['id']}/verification-evidence",
        json={
            "project_id": project["id"],
            "title": "Verification evidence",
            "evidence_type": VerificationEvidenceType.test_result.value,
            "summary": "Demo evidence",
            "source_name": "Lab report",
            "source_reference": "LR-001",
            "linked_requirement_ids": [requirement["id"]],
            "linked_test_case_ids": [test_case["id"]],
            "linked_component_ids": [],
            "linked_non_conformity_ids": [],
        },
    )
    assert verification_create.status_code == 201
    verification = verification_create.json()

    verification_list = client.get(f"/api/projects/{project['id']}/verification-evidence")
    assert verification_list.status_code == 200

    verification_detail = client.get(f"/api/verification-evidence/{verification['id']}")
    assert verification_detail.status_code == 200
    assert "linked_objects" in verification_detail.json()

    bad_verification = client.post(
        f"/api/projects/{project['id']}/verification-evidence",
        json={
            "project_id": str(uuid4()),
            "title": "Mismatched evidence",
            "evidence_type": VerificationEvidenceType.test_result.value,
            "summary": "Demo",
        },
    )
    assert bad_verification.status_code == 400

    simulation_create = client.post(
        f"/api/projects/{project['id']}/simulation-evidence",
        json={
            "project_id": project["id"],
            "title": "Simulation evidence",
            "model_reference": "MODEL-1",
            "scenario_name": "Nominal climb",
            "input_summary": "Inputs",
            "inputs_json": {"altitude": 1000},
            "expected_behavior": "Stable",
            "observed_behavior": "Stable",
            "result": SimulationEvidenceResult.passed.value,
            "execution_timestamp": "2026-04-01T10:00:00Z",
            "fmi_contract_id": None,
            "metadata_json": {},
            "linked_requirement_ids": [requirement["id"]],
            "linked_test_case_ids": [test_case["id"]],
            "linked_verification_evidence_ids": [verification["id"]],
        },
    )
    assert simulation_create.status_code == 201
    simulation = simulation_create.json()

    simulation_list = client.get(f"/api/projects/{project['id']}/simulation-evidence")
    assert simulation_list.status_code == 200

    simulation_detail = client.get(f"/api/simulation-evidence/{simulation['id']}")
    assert simulation_detail.status_code == 200

    operational_create = client.post(
        f"/api/projects/{project['id']}/operational-evidence",
        json={
            "project_id": project["id"],
            "title": "Operational evidence",
            "source_name": "Flight log",
            "source_type": OperationalEvidenceSourceType.sensor.value,
            "captured_at": "2026-04-01T10:00:00Z",
            "coverage_window_start": "2026-04-01T09:00:00Z",
            "coverage_window_end": "2026-04-01T10:00:00Z",
            "observations_summary": "Nominal",
            "aggregated_observations_json": {"temp": 30},
            "quality_status": OperationalEvidenceQualityStatus.good.value,
            "derived_metrics_json": {"battery": 80},
            "metadata_json": {},
            "linked_requirement_ids": [requirement["id"]],
            "linked_verification_evidence_ids": [verification["id"]],
        },
    )
    assert operational_create.status_code == 201
    operational = operational_create.json()

    operational_list = client.get(f"/api/projects/{project['id']}/operational-evidence")
    assert operational_list.status_code == 200

    operational_detail = client.get(f"/api/operational-evidence/{operational['id']}")
    assert operational_detail.status_code == 200

    test_run_create = client.post(
        "/api/test-runs",
        json={
            "test_case_id": test_case["id"],
            "execution_date": "2026-04-01",
            "result": "passed",
            "summary": "Pass",
            "measured_values_json": {"value": 1},
            "notes": "ok",
            "executed_by": "tester",
        },
    )
    assert test_run_create.status_code == 201

    test_run_list = client.get("/api/test-runs", params={"project_id": project["id"]})
    assert test_run_list.status_code == 200

    operational_run_create = client.post(
        "/api/operational-runs",
        json={
            "project_id": project["id"],
            "key": "RUN-001",
            "date": "2026-04-01",
            "drone_serial": "DRONE-001",
            "location": "Field",
            "duration_minutes": 45,
            "max_temperature_c": 40.0,
            "battery_consumption_pct": 20.0,
            "outcome": OperationalOutcome.success.value,
            "notes": "Nominal",
            "telemetry_json": {"speed": 12},
        },
    )
    assert operational_run_create.status_code == 201
    operational_run = operational_run_create.json()

    operational_run_list = client.get("/api/operational-runs", params={"project_id": project["id"]})
    assert operational_run_list.status_code == 200

    operational_run_detail = client.get(f"/api/operational-runs/{operational_run['id']}")
    assert operational_run_detail.status_code == 200
    assert "links" in operational_run_detail.json()

    operational_run_patch = client.patch(
        f"/api/operational-runs/{operational_run['id']}",
        json={"outcome": OperationalOutcome.degraded.value},
    )
    assert operational_run_patch.status_code == 200
    assert operational_run_patch.json()["outcome"] == OperationalOutcome.degraded.value

    fmi_create = client.post(
        f"/api/projects/{project['id']}/fmi-contracts",
        json={
            "project_id": project["id"],
            "key": "FMI-001",
            "name": "FMI contract",
            "description": "Demo",
            "model_identifier": "model://demo",
            "model_version": "1.0",
            "model_uri": "file:///tmp/demo.fmu",
            "adapter_profile": "fmi-placeholder",
            "contract_version": "fmi.placeholder.v1",
            "metadata_json": {},
        },
    )
    assert fmi_create.status_code == 201
    fmi_contract = fmi_create.json()

    fmi_list = client.get(f"/api/projects/{project['id']}/fmi-contracts")
    assert fmi_list.status_code == 200

    fmi_detail = client.get(f"/api/fmi-contracts/{fmi_contract['id']}")
    assert fmi_detail.status_code == 200
    assert "simulation_evidence" in fmi_detail.json()

    import_response = client.post(
        f"/api/projects/{project['id']}/imports",
        json={
            "format": "json",
            "content": json.dumps(
                {
                    "records": [
                        {
                            "type": "external_artifact",
                            "external_id": "REQ-EXT-1",
                            "artifact_type": "requirement",
                            "name": "Imported requirement",
                        }
                    ]
                }
            ),
        },
    )
    assert import_response.status_code == 201
    assert import_response.json()["summary"]["parsed_records"] > 0


def test_connectors_external_artifacts_links_sysml_and_analysis_endpoints(client: TestClient):
    project = client.post("/api/projects", json={"code": "REL-PRJ", "name": "Relations Project", "description": "Demo"}).json()

    requirement = client.post(
        "/api/requirements",
        json={
            "project_id": project["id"],
            "key": "REQ-REL-001",
            "title": "Traceable requirement",
            "category": RequirementCategory.performance.value,
            "priority": Priority.high.value,
            "verification_method": VerificationMethod.test.value,
        },
    ).json()
    client.post(f"/api/requirements/{requirement['id']}/submit-review")
    client.post(f"/api/requirements/{requirement['id']}/approve")

    block = client.post(
        "/api/blocks",
        json={
            "project_id": project["id"],
            "key": "BLK-REL-001",
            "name": "Traceable block",
            "block_kind": BlockKind.system.value,
            "abstraction_level": AbstractionLevel.logical.value,
        },
    ).json()

    test_case = client.post(
        "/api/test-cases",
        json={
            "project_id": project["id"],
            "key": "TST-REL-001",
            "title": "Traceability test",
            "method": TestMethod.simulation.value,
            "status": TestCaseStatus.draft.value,
        },
    ).json()

    connector = client.post(
        f"/api/projects/{project['id']}/connectors",
        json={
            "project_id": project["id"],
            "name": "DOORS NG",
            "connector_type": ConnectorType.doors.value,
            "base_url": "https://doors.example.local",
            "description": "Requirements source",
            "is_active": True,
            "metadata_json": {},
        },
    )
    assert connector.status_code == 201
    connector_id = connector.json()["id"]

    connectors_list = client.get(f"/api/projects/{project['id']}/connectors")
    assert connectors_list.status_code == 200

    connector_detail = client.get(f"/api/connectors/{connector_id}")
    assert connector_detail.status_code == 200

    artifact = client.post(
        f"/api/projects/{project['id']}/external-artifacts",
        json={
            "project_id": project["id"],
            "connector_definition_id": connector_id,
            "external_id": "EXT-REQ-001",
            "artifact_type": ExternalArtifactType.requirement.value,
            "name": "External requirement",
            "description": "Demo",
            "canonical_uri": "https://example.local/ext/req/1",
            "native_tool_url": "https://doors.example.local/req/1",
            "status": "active",
            "metadata_json": {},
        },
    )
    assert artifact.status_code == 201
    artifact_id = artifact.json()["id"]

    artifact_list = client.get(f"/api/projects/{project['id']}/external-artifacts", params={"artifact_type": ExternalArtifactType.requirement.value})
    assert artifact_list.status_code == 200

    version = client.post(
        f"/api/external-artifacts/{artifact_id}/versions",
        json={
            "version_label": "1",
            "revision_label": "A",
            "checksum_or_signature": "abc123",
            "metadata_json": {},
        },
    )
    assert version.status_code == 201

    version_list = client.get(f"/api/external-artifacts/{artifact_id}/versions")
    assert version_list.status_code == 200

    artifact_link = client.post(
        f"/api/projects/{project['id']}/artifact-links",
        json={
            "project_id": project["id"],
            "internal_object_type": FederatedInternalObjectType.block.value,
            "internal_object_id": block["id"],
            "external_artifact_id": artifact_id,
            "external_artifact_version_id": None,
            "relation_type": ArtifactLinkRelationType.maps_to.value,
            "rationale": "Trace to source artifact",
        },
    )
    assert artifact_link.status_code == 201
    artifact_link_id = artifact_link.json()["id"]

    artifact_links = client.get(f"/api/projects/{project['id']}/artifact-links")
    assert artifact_links.status_code == 200

    delete_artifact_link = client.delete(f"/api/artifact-links/{artifact_link_id}")
    assert delete_artifact_link.status_code == 204

    link = client.post(
        "/api/links",
        json={
            "project_id": project["id"],
            "source_type": LinkObjectType.requirement.value,
            "source_id": requirement["id"],
            "target_type": LinkObjectType.test_case.value,
            "target_id": test_case["id"],
            "relation_type": RelationType.verifies.value,
            "rationale": "Requirement is verified by test",
        },
    )
    assert link.status_code == 201
    link_id = link.json()["id"]

    links = client.get("/api/links", params={"project_id": project["id"]})
    assert links.status_code == 200

    delete_link = client.delete(f"/api/links/{link_id}")
    assert delete_link.status_code == 204

    sysml_relation = client.post(
        "/api/sysml-relations",
        json={
            "project_id": project["id"],
            "source_type": SysMLObjectType.block.value,
            "source_id": block["id"],
            "target_type": SysMLObjectType.requirement.value,
            "target_id": requirement["id"],
            "relation_type": SysMLRelationType.satisfy.value,
            "rationale": "Block satisfies requirement",
        },
    )
    assert sysml_relation.status_code == 201
    sysml_relation_id = sysml_relation.json()["id"]

    sysml_relations = client.get("/api/sysml-relations", params={"project_id": project["id"]})
    assert sysml_relations.status_code == 200

    delete_sysml_relation = client.delete(f"/api/sysml-relations/{sysml_relation_id}")
    assert delete_sysml_relation.status_code == 204

    child_block = client.post(
        "/api/blocks",
        json={
            "project_id": project["id"],
            "key": "BLK-REL-002",
            "name": "Child block",
            "block_kind": BlockKind.component.value,
            "abstraction_level": AbstractionLevel.physical.value,
        },
    ).json()

    containment = client.post(
        "/api/block-containments",
        json={
            "project_id": project["id"],
            "parent_block_id": block["id"],
            "child_block_id": child_block["id"],
            "relation_type": BlockContainmentRelationType.contains.value,
        },
    )
    assert containment.status_code == 201
    containment_id = containment.json()["id"]

    delete_containment = client.delete(f"/api/block-containments/{containment_id}")
    assert delete_containment.status_code == 204

    block_tree = client.get(f"/api/projects/{project['id']}/sysml/block-tree")
    assert block_tree.status_code == 200

    satisfaction = client.get(f"/api/projects/{project['id']}/sysml/satisfaction")
    assert satisfaction.status_code == 200

    verification = client.get(f"/api/projects/{project['id']}/sysml/verification")
    assert verification.status_code == 200

    derivations = client.get(f"/api/projects/{project['id']}/sysml/derivations")
    assert derivations.status_code == 200

    mapping_contract = client.get(f"/api/projects/{project['id']}/sysml/mapping-contract")
    assert mapping_contract.status_code == 200
    assert mapping_contract.json()["contract_schema"] == "threadlite.sysml.mapping-contract.v1"

    step_ap242 = client.get(f"/api/projects/{project['id']}/step-ap242-contract")
    assert step_ap242.status_code == 200
    assert step_ap242.json()["contract_schema"] == "threadlite.step.ap242.contract.v1"

    matrix = client.get(f"/api/projects/{project['id']}/matrix", params={"mode": "components"})
    assert matrix.status_code == 200

    impact = client.get(f"/api/projects/{project['id']}/impact/requirement/{requirement['id']}")
    assert impact.status_code == 200
    body = impact.json()
    assert "direct" in body and "secondary" in body

    export_response = client.get(f"/api/projects/{project['id']}/export")
    assert export_response.status_code == 200
    assert "Content-Disposition" in export_response.headers
    exported = export_response.json()
    assert exported["schema"] == "threadlite.project.export.v1"
