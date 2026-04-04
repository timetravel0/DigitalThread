from datetime import datetime, timedelta, timezone
import json

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    ArtifactLinkRelationType,
    AbstractionLevel,
    Block,
    BlockContainmentRelationType,
    BlockKind,
    BlockStatus,
    ChangeRequestStatus,
    Component,
    ComponentStatus,
    ComponentType,
    ConfigurationContext,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConnectorType,
    ExternalArtifactType,
    ExternalArtifactStatus,
    FederatedInternalObjectType,
    ImpactLevel,
    Link,
    LinkObjectType,
    NonConformityStatus,
    NonConformityDisposition,
    OperationalOutcome,
    OperationalEvidence,
    OperationalEvidenceLinkObjectType,
    OperationalEvidenceQualityStatus,
    OperationalEvidenceSourceType,
    Priority,
    Project,
    RelationType,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    RequirementVerificationStatus,
    Severity,
    RevisionSnapshot,
    SimulationEvidenceResult,
    SysMLObjectType,
    SysMLRelation,
    SysMLRelationType,
    TestCase,
    TestCaseStatus,
    TestMethod,
    TestRunResult,
    VerificationEvidenceType,
    VerificationMethod,
)
from app.schemas import (
    ArtifactLinkCreate,
    BlockCreate,
    BlockContainmentCreate,
    BaselineCreate,
    FMIContractCreate,
    ConfigurationContextCreate,
    ConfigurationItemMappingCreate,
    ConfigurationContextUpdate,
    ChangeImpactCreate,
    ChangeRequestCreate,
    ChangeRequestUpdate,
    NonConformityCreate,
    NonConformityUpdate,
    LinkCreate,
    ExternalArtifactCreate,
    ExternalArtifactVersionCreate,
    ProjectImportCreate,
    OperationalEvidenceCreate,
    OperationalRunCreate,
    OperationalRunUpdate,
    ProjectCreate,
    RequirementCreate,
    RequirementUpdate,
    TestRunCreate,
    SysMLRelationCreate,
    SimulationEvidenceCreate,
    TestCaseCreate,
    VerificationEvidenceCreate,
    WorkflowActionPayload,
    ComponentCreate,
    ConnectorDefinitionCreate,
)
from app.services import (
    approve_requirement,
    approve_change_request,
    build_impact,
    build_sysml_mapping_contract,
    compare_configuration_contexts,
    compare_baselines,
    compare_baseline_to_configuration_context,
    create_configuration_context,
    create_configuration_item_mapping,
    create_baseline,
    create_block_containment,
    create_artifact_link,
    create_block,
    create_change_impact,
    create_change_request,
    create_non_conformity,
    create_operational_evidence,
    delete_configuration_item_mapping,
    create_link,
    create_component,
    create_connector,
    create_project,
    create_requirement,
    create_external_artifact,
    create_external_artifact_version,
    create_operational_run,
    create_simulation_evidence,
    import_project_records,
    create_requirement_draft_version,
    create_sysml_relation,
    create_test_run,
    create_test_case,
    create_verification_evidence,
    build_step_ap242_contract,
    create_fmi_contract,
    export_project_bundle,
    get_baseline_detail,
    get_baseline_bridge_context,
    get_component_detail,
    get_fmi_contract_service,
    get_configuration_context_service,
    get_authoritative_registry_summary,
    get_change_request_detail,
    get_non_conformity_detail,
    get_operational_run_detail,
    get_operational_evidence_service,
    get_requirement_detail,
    get_simulation_evidence_service,
    get_test_case_detail,
    get_project_dashboard,
    list_requirement_history,
    list_fmi_contracts,
    list_operational_evidence,
    reject_requirement,
    reject_change_request,
    close_change_request,
    mark_change_request_implemented,
    reopen_change_request,
    submit_change_request_for_analysis,
    seed_demo,
    submit_requirement_for_review,
    update_requirement,
    update_configuration_context,
    update_non_conformity,
    update_operational_run,
    update_change_request,
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
        req1 = session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "DR-REQ-001")).one()
        req2 = session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "DR-REQ-002")).one()
        req3 = session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "DR-REQ-003")).one()
        req4 = session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == "DR-REQ-004")).one()

        req1_detail = get_requirement_detail(session, req1.id)
        req2_detail = get_requirement_detail(session, req2.id)
        req3_detail = get_requirement_detail(session, req3.id)
        req4_detail = get_requirement_detail(session, req4.id)

        assert dashboard.kpis.total_requirements == 6
        assert dashboard.kpis.requirements_with_allocated_components == 5
        assert dashboard.kpis.requirements_with_verifying_tests == 4
        assert dashboard.kpis.requirements_at_risk == 2
        assert dashboard.kpis.failed_tests_last_30_days == 1
        assert dashboard.kpis.open_change_requests == 1
        assert req1_detail["verification_evaluation"].status == RequirementVerificationStatus.failed
        assert req2_detail["verification_evaluation"].status == RequirementVerificationStatus.verified
        assert req3_detail["verification_evaluation"].status == RequirementVerificationStatus.verified
        assert req4_detail["verification_evaluation"].status == RequirementVerificationStatus.at_risk


def test_verification_evidence_explicit_signals_override_test_run_compatibility():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-VER-SIGNAL", name="Verification Signals", description=""))

        verified_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-VERIFIED-SIGNAL",
                title="Explicit verified signal requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        verified_test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-VERIFIED-SIGNAL",
                title="Explicit verified signal test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Verified evidence record",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Verification result passed.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[verified_requirement.id],
                linked_test_case_ids=[verified_test_case.id],
                metadata_json={"verification": {"result": "passed"}},
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=verified_requirement.id,
                target_type=LinkObjectType.test_case,
                target_id=verified_test_case.id,
                relation_type=RelationType.verifies,
                rationale="Verification evidence supports the requirement.",
            ),
        )
        create_test_run(
            session,
            TestRunCreate(
                test_case_id=verified_test_case.id,
                execution_date=datetime.now(timezone.utc).date(),
                result=TestRunResult.failed,
                summary="Legacy run failed.",
                measured_values_json={},
                notes="",
            ),
        )
        assert get_requirement_detail(session, verified_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.verified

        failed_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-FAILED-SIGNAL",
                title="Explicit failed signal requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        failed_test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-FAILED-SIGNAL",
                title="Explicit failed signal test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Failed evidence record",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Verification result failed.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[failed_requirement.id],
                linked_test_case_ids=[failed_test_case.id],
                metadata_json={"verification": {"result": "failed"}},
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=failed_requirement.id,
                target_type=LinkObjectType.test_case,
                target_id=failed_test_case.id,
                relation_type=RelationType.verifies,
                rationale="Verification evidence supports the requirement.",
            ),
        )
        create_test_run(
            session,
            TestRunCreate(
                test_case_id=failed_test_case.id,
                execution_date=datetime.now(timezone.utc).date(),
                result=TestRunResult.passed,
                summary="Legacy run passed.",
                measured_values_json={},
                notes="",
            ),
        )
        assert get_requirement_detail(session, failed_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.failed


def test_verification_status_explainability_and_dashboard_breakdown():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-VER-UX", name="Verification UX", description=""))

        not_covered = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-UX-NC",
                title="Uncovered requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )

        partial = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-UX-PART",
                title="Partial requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Partial evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Coverage is incomplete and pending additional review.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[partial.id],
            ),
        )

        at_risk = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-UX-RISK",
                title="Risk requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.analysis,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Risk evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Warning: unstable trend and degraded evidence quality.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[at_risk.id],
            ),
        )

        failed = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-UX-FAIL",
                title="Failed requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.analysis,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Failed evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Verification failed because the harness broke.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[failed.id],
            ),
        )

        verified = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-UX-VER",
                title="Verified requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.analysis,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Verified evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Verification result passed with no open issues.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[verified.id],
                metadata_json={"verification": {"result": "passed"}},
            ),
        )

        dashboard = get_project_dashboard(session, project.id)
        assert dashboard.verification_status_breakdown.not_covered == 1
        assert dashboard.verification_status_breakdown.partially_verified == 1
        assert dashboard.verification_status_breakdown.at_risk == 1
        assert dashboard.verification_status_breakdown.failed == 1
        assert dashboard.verification_status_breakdown.verified == 1

        evaluation = get_requirement_detail(session, verified.id)["verification_evaluation"]
        assert evaluation.decision_source == "verification evidence"
        assert evaluation.decision_summary
        assert evaluation.status == RequirementVerificationStatus.verified


def test_requirement_verification_status_engine_uses_evidence_and_test_runs():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-VER", name="Verification", description=""))

        not_covered = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-NC",
                title="No evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        assert get_requirement_detail(session, not_covered.id)["verification_evaluation"].status == RequirementVerificationStatus.not_covered

        partial_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-PART",
                title="Partial evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Partial evidence",
                evidence_type=VerificationEvidenceType.test_result,
                summary="Evidence exists but no linked test execution is attached.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[partial_requirement.id],
                linked_test_case_ids=[],
            ),
        )
        assert get_requirement_detail(session, partial_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.partially_verified

        failed_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-FAIL",
                title="Failed evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        failed_test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-FAIL",
                title="Failed verification test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Failed evidence",
                evidence_type=VerificationEvidenceType.test_result,
                summary="Evidence linked to a failed run.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[failed_requirement.id],
                linked_test_case_ids=[failed_test_case.id],
            ),
        )
        create_test_run(
            session,
            TestRunCreate(
                test_case_id=failed_test_case.id,
                execution_date=datetime.now(timezone.utc).date(),
                result=TestRunResult.failed,
                summary="Latest run failed.",
                measured_values_json={},
                notes="",
            ),
        )
        assert get_requirement_detail(session, failed_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.failed

        at_risk_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-RISK",
                title="Stale evidence requirement",
                category=RequirementCategory.compliance,
                priority=Priority.medium,
                verification_method=VerificationMethod.analysis,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Stale evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Evidence is too old to be trusted as current.",
                observed_at=datetime.now(timezone.utc) - timedelta(days=60),
                linked_requirement_ids=[at_risk_requirement.id],
                linked_test_case_ids=[],
            ),
        )
        assert get_requirement_detail(session, at_risk_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.at_risk

        verified_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-OK",
                title="Fresh evidence requirement",
                category=RequirementCategory.compliance,
                priority=Priority.medium,
                verification_method=VerificationMethod.analysis,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Fresh evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Fresh evidence closes the loop.",
                observed_at=datetime.now(timezone.utc),
                linked_requirement_ids=[verified_requirement.id],
                linked_test_case_ids=[],
            ),
        )
        assert get_requirement_detail(session, verified_requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.verified


def test_verification_evidence_naive_observed_at_does_not_break_requirement_evaluation():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-VER-TZ", name="Verification TZ", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-TZ",
                title="Timezone evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Naive observed_at evidence",
                evidence_type=VerificationEvidenceType.analysis,
                summary="Naive timestamp should still be treated as UTC-safe.",
                observed_at=datetime.now().replace(microsecond=0),
                linked_requirement_ids=[requirement.id],
            ),
        )

        detail = get_requirement_detail(session, requirement.id)
        assert detail["verification_evaluation"].status == RequirementVerificationStatus.partially_verified
        assert detail["verification_evaluation"].fresh_evidence_count == 1


def test_operational_run_detail_and_requirement_status_track_reports_on_links():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-OPS", name="Operations", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-OPS",
                title="Operational endurance requirement",
                category=RequirementCategory.operations,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        run = create_operational_run(
            session,
            OperationalRunCreate(
                project_id=project.id,
                key="RUN-001",
                date=datetime.now(timezone.utc).date(),
                drone_serial="DRN-2001",
                location="Field test range",
                duration_minutes=18,
                max_temperature_c=28.4,
                battery_consumption_pct=72,
                outcome=OperationalOutcome.success,
                notes="Nominal flight with clean telemetry.",
                telemetry_json={"altitude_m": 54, "battery_pct": 72, "signal_strength": "good"},
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.operational_run,
                source_id=run.id,
                target_type=LinkObjectType.requirement,
                target_id=requirement.id,
                relation_type=RelationType.reports_on,
                rationale="Operational telemetry supports the requirement.",
            ),
        )

        detail = get_operational_run_detail(session, run.id)
        assert detail["operational_run"].telemetry_json["altitude_m"] == 54
        assert any(link.target_label == requirement.key for link in detail["links"])
        assert get_requirement_detail(session, requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.verified

        update_operational_run(
            session,
            run.id,
            OperationalRunUpdate(
                outcome=OperationalOutcome.failure,
                telemetry_json={"altitude_m": 19, "battery_pct": 12, "signal_strength": "poor"},
            ),
        )
        assert get_requirement_detail(session, requirement.id)["verification_evaluation"].status == RequirementVerificationStatus.failed


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


def test_sysml_mapping_contract_exposes_requirement_and_block_semantics():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P2-SYSML", name="P2-SYSML", description=""))
        base_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-BASE",
                title="Base requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        derived_requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-DERIVED",
                title="Derived requirement",
                category=RequirementCategory.performance,
                priority=Priority.medium,
                verification_method=VerificationMethod.analysis,
                status=RequirementStatus.approved,
            ),
        )
        logical_block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-LOG",
                name="Logical block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
            ),
        )
        physical_block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-PHY",
                name="Physical block",
                block_kind=BlockKind.assembly,
                abstraction_level=AbstractionLevel.physical,
                status=BlockStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-SYSML",
                title="SysML verification",
                method=TestMethod.simulation,
                status=TestCaseStatus.approved,
            ),
        )

        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.block,
                source_id=logical_block.id,
                target_type=SysMLObjectType.requirement,
                target_id=base_requirement.id,
                relation_type=SysMLRelationType.satisfy,
            ),
        )
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.test_case,
                source_id=test_case.id,
                target_type=SysMLObjectType.requirement,
                target_id=base_requirement.id,
                relation_type=SysMLRelationType.verify,
            ),
        )
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.requirement,
                source_id=base_requirement.id,
                target_type=SysMLObjectType.requirement,
                target_id=derived_requirement.id,
                relation_type=SysMLRelationType.deriveReqt,
            ),
        )
        create_block_containment(
            session,
            BlockContainmentCreate(
                project_id=project.id,
                parent_block_id=logical_block.id,
                child_block_id=physical_block.id,
                relation_type=BlockContainmentRelationType.contains,
            ),
        )

        contract = build_sysml_mapping_contract(session, project.id)

        assert contract.contract_schema == "threadlite.sysml.mapping-contract.v1"
        assert contract.summary.requirement_count == 2
        assert contract.summary.block_count == 2
        assert contract.summary.logical_block_count == 1
        assert contract.summary.physical_block_count == 1
        assert contract.summary.satisfy_relation_count == 1
        assert contract.summary.verify_relation_count == 1
        assert contract.summary.derive_relation_count == 1
        assert contract.summary.contain_relation_count == 1

        base_row = next(row for row in contract.requirements if row.requirement.id == base_requirement.id)
        assert any(block.object_id == logical_block.id for block in base_row.satisfy_blocks)
        assert any(test.object_id == test_case.id for test in base_row.verify_tests)
        derived_row = next(row for row in contract.requirements if row.requirement.id == derived_requirement.id)
        assert any(source.object_id == base_requirement.id for source in derived_row.derived_from)

        logical_row = next(row for row in contract.blocks if row.block.id == logical_block.id)
        assert logical_row.abstraction_level == AbstractionLevel.logical
        assert any(child.object_id == physical_block.id for child in logical_row.contained_blocks)
        assert any(req.object_id == base_requirement.id for req in logical_row.satisfies_requirements)

        bundle = export_project_bundle(session, project.id)
        assert bundle["sysml_mapping_contract"]["summary"]["satisfy_relation_count"] == 1


def test_step_ap242_contract_exposes_part_metadata_and_links():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P2-AP242", name="P2-AP242", description=""))
        component = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="CMP-AP242",
                name="Battery Pack",
                description="Physical battery assembly",
                type=ComponentType.battery,
                part_number="BAT-3000",
                supplier="VoltCraft",
                status=ComponentStatus.selected,
                version=2,
                metadata_json={"mass_kg": 1.2},
            ),
        )
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(project_id=project.id, name="Teamcenter PLM", connector_type=ConnectorType.plm),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="PLM-PART-DR-BATT-01",
                artifact_type=ExternalArtifactType.cad_part,
                name="Battery Pack Assembly",
                canonical_uri="plm://PLM-PART-DR-BATT-01",
                native_tool_url="https://teamcenter.example.local/items/PLM-PART-DR-BATT-01",
                status=ExternalArtifactStatus.active,
            ),
        )
        version = create_external_artifact_version(
            session,
            artifact.id,
            ExternalArtifactVersionCreate(version_label="C", revision_label="C", metadata_json={"supplier": "VoltCraft"}),
        )
        create_artifact_link(
            session,
            ArtifactLinkCreate(
                project_id=project.id,
                internal_object_type=FederatedInternalObjectType.component,
                internal_object_id=component.id,
                external_artifact_id=artifact.id,
                relation_type=ArtifactLinkRelationType.maps_to,
            ),
        )

        contract = build_step_ap242_contract(session, project.id)

        assert contract.contract_schema == "threadlite.step.ap242.contract.v1"
        assert contract.summary.physical_component_count == 1
        assert contract.summary.cad_artifact_count == 1
        assert contract.summary.linked_cad_artifact_count == 1
        assert contract.summary.identifier_count >= 3
        assert contract.parts[0].component.id == component.id
        assert contract.parts[0].part_number == "BAT-3000"
        assert any(identifier.kind == "part_number" for identifier in contract.parts[0].identifiers)
        assert contract.parts[0].linked_cad_artifacts[0].id == artifact.id
        assert contract.relations[0].relation_type == ArtifactLinkRelationType.maps_to.value
        assert contract.relations[0].cad_artifact.id == artifact.id
        assert version.external_artifact_id == artifact.id
        bundle = export_project_bundle(session, project.id)
        assert bundle["step_ap242_contract"]["summary"]["cad_artifact_count"] == 1


def test_impact_analysis_includes_blocks_and_tests_from_sysml_relations():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        req = session.exec(select(Requirement).where(Requirement.key == "DR-REQ-001")).one()
        impact = build_impact(session, project.id, "requirement", req.id)

        assert any(item.object_type == "block" for item in impact.direct)
        assert any(item.object_type == "test_case" for item in impact.secondary + impact.direct)
        assert impact.related_baselines


def test_graph_aware_impact_traversal_walks_cycles_and_respects_active_context_for_evidence():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-GRAPH-1", name="P-GRAPH-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-GRAPH",
                title="Graph root requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-GRAPH",
                name="Graph block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-GRAPH",
                title="Graph test",
                method=TestMethod.simulation,
                status=TestCaseStatus.approved,
            ),
        )
        component = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="CMP-GRAPH",
                name="Graph component",
                type=ComponentType.software_module,
                status=ComponentStatus.validated,
                version=2,
            ),
        )
        excluded_component = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="CMP-OUT",
                name="Outside context component",
                type=ComponentType.other,
                status=ComponentStatus.selected,
                version=1,
            ),
        )
        baseline = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Graph baseline",
                description="Baseline used in the traversal test",
                requirement_ids=[requirement.id],
                block_ids=[],
                test_case_ids=[],
            ),
        )[0]
        change_request = create_change_request(
            session,
            ChangeRequestCreate(
                project_id=project.id,
                key="CR-GRAPH",
                title="Graph change",
                description="Traverse to a downstream change request",
                severity=Severity.medium,
            ),
        )

        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.requirement,
                source_id=requirement.id,
                target_type=SysMLObjectType.block,
                target_id=block.id,
                relation_type=SysMLRelationType.trace,
            ),
        )
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.block,
                source_id=block.id,
                target_type=SysMLObjectType.test_case,
                target_id=test_case.id,
                relation_type=SysMLRelationType.trace,
            ),
        )
        create_sysml_relation(
            session,
            SysMLRelationCreate(
                project_id=project.id,
                source_type=SysMLObjectType.test_case,
                source_id=test_case.id,
                target_type=SysMLObjectType.requirement,
                target_id=requirement.id,
                relation_type=SysMLRelationType.verify,
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.test_case,
                source_id=test_case.id,
                target_type=LinkObjectType.component,
                target_id=component.id,
                relation_type=RelationType.uses,
                rationale="Software realization relationship.",
            ),
        )
        create_change_impact(
            session,
            ChangeImpactCreate(
                change_request_id=change_request.id,
                object_type="component",
                object_id=component.id,
                impact_level=ImpactLevel.high,
                notes="The component is downstream of the requirement thread.",
            ),
        )
        create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-GRAPH",
                name="Graph context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        context = session.exec(
            select(ConfigurationContext).where(ConfigurationContext.project_id == project.id, ConfigurationContext.key == "CTX-GRAPH")
        ).one()
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.baseline_item,
                internal_object_type=FederatedInternalObjectType.component,
                internal_object_id=component.id,
                internal_object_version=component.version,
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Graph evidence",
                evidence_type=VerificationEvidenceType.telemetry,
                summary="Evidence tied to the active thread.",
                observed_at=datetime.now(timezone.utc),
                source_name="Flight software",
                source_reference="EV-1",
                linked_component_ids=[component.id],
            ),
        )
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Excluded evidence",
                evidence_type=VerificationEvidenceType.telemetry,
                summary="Should be ignored by active context filtering.",
                observed_at=datetime.now(timezone.utc),
                source_name="External software",
                source_reference="EV-2",
                linked_component_ids=[excluded_component.id],
            ),
        )

        impact = build_impact(session, project.id, "requirement", requirement.id)

        assert any(item.object_type == "block" for item in impact.direct)
        assert any(item.object_type == "test_case" for item in impact.direct)
        assert any(item.object_type == "component" for item in impact.secondary)
        assert any(item.object_type == "baseline" for item in impact.likely_impacted)
        assert any(item.object_type == "change_request" for item in impact.likely_impacted)
        assert any(item.object_type == "verification_evidence" for item in impact.likely_impacted)
        assert all(item.label != "Excluded evidence" for item in impact.likely_impacted)
        assert all(item.object_id != requirement.id for item in impact.likely_impacted)


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
        assert bundle["non_conformities"]
        assert any(item["key"] == "NC-001" for item in bundle["non_conformities"])
        assert bundle["baselines"]
        assert bundle["revision_snapshots"]


def test_baseline_and_configuration_context_bridge_expose_related_objects():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-BRIDGE-1", name="P-BRIDGE-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-BRIDGE",
                title="Bridge requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-BRIDGE",
                name="Bridge block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-BRIDGE",
                title="Bridge test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Bridge baseline",
                description="Baseline linked to a context",
                requirement_ids=[requirement.id],
                block_ids=[block.id],
                test_case_ids=[test_case.id],
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-BRIDGE",
                name="Bridge context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_block,
                internal_object_type=FederatedInternalObjectType.block,
                internal_object_id=block.id,
                internal_object_version=block.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_test_case,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=test_case.id,
                internal_object_version=test_case.version,
            ),
        )

        baseline_detail = get_baseline_detail(session, baseline.id)
        bridge_context = get_baseline_bridge_context(session, baseline.id)
        context_detail = get_configuration_context_service(session, context.id)

        assert baseline_detail["related_configuration_contexts"]
        assert baseline_detail["related_configuration_contexts"][0].id == context.id
        assert baseline_detail["bridge_context"].baseline_id == baseline.id
        assert bridge_context.baseline_id == baseline.id
        assert bridge_context.item_count == 3
        assert context_detail["related_baselines"]
        assert context_detail["related_baselines"][0].id == baseline.id


def test_configuration_context_compare_groups_added_removed_and_version_changes_by_kind():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P3", name="P3", description=""))
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
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                external_id="ART-1",
                artifact_type=ExternalArtifactType.document,
                name="Artifact",
            ),
        )
        artifact_v1 = create_external_artifact_version(session, artifact.id, ExternalArtifactVersionCreate(version_label="v1"))
        left_context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-1",
                name="Left",
                status=ConfigurationContextStatus.active,
                context_type=ConfigurationContextType.review_gate,
            ),
        )
        create_configuration_item_mapping(
            session,
            left_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            left_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=artifact_v1.id,
            ),
        )

        update_requirement(session, requirement.id, RequirementUpdate(version=2))
        artifact_v2 = create_external_artifact_version(session, artifact.id, ExternalArtifactVersionCreate(version_label="v2"))
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-1",
                name="Block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
            ),
        )
        right_context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-2",
                name="Right",
                status=ConfigurationContextStatus.active,
                context_type=ConfigurationContextType.review_gate,
            ),
        )
        requirement = update_requirement(session, requirement.id, RequirementUpdate(version=2))
        create_configuration_item_mapping(
            session,
            right_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            right_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=artifact_v2.id,
            ),
        )
        create_configuration_item_mapping(
            session,
            right_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_block,
                internal_object_type=FederatedInternalObjectType.block,
                internal_object_id=block.id,
                internal_object_version=block.version,
            ),
        )

        comparison = compare_configuration_contexts(session, left_context.id, right_context.id)

        assert comparison.summary.added == 1
        assert comparison.summary.removed == 0
        assert comparison.summary.version_changed == 2
        assert comparison.groups == sorted(comparison.groups, key=lambda group: list(ConfigurationItemKind).index(group.item_kind))

        requirement_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_requirement)
        assert requirement_group.version_changed[0].left.object_version == 1
        assert requirement_group.version_changed[0].right.object_version == 2

        artifact_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.external_artifact_version)
        assert artifact_group.version_changed[0].left.external_artifact_version_id == artifact_v1.id
        assert artifact_group.version_changed[0].right.external_artifact_version_id == artifact_v2.id
        assert artifact_group.version_changed[0].left.connector_name == "Cameo"
        assert artifact_group.version_changed[0].left.artifact_name == "Compare artifact"
        assert artifact_group.version_changed[0].left.version_label == "1.0"
        assert artifact_group.version_changed[0].left.revision_label is None
        assert artifact_group.version_changed[0].right.connector_name == "Cameo"
        assert artifact_group.version_changed[0].right.artifact_name == "Compare artifact"
        assert artifact_group.version_changed[0].right.version_label == "2.0"
        assert artifact_group.version_changed[0].right.revision_label is None

        block_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_block)
        assert block_group.added[0].object_id == block.id


def test_change_request_lifecycle_tracks_history_and_rejects_direct_status_edits():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-CR-1", name="P-CR-1", description=""))

        with pytest.raises(ValueError):
            create_change_request(
                session,
                ChangeRequestCreate(
                    project_id=project.id,
                    key="CR-BAD",
                    title="Bad state",
                    description="Should not be creatable outside open state",
                    severity=Severity.medium,
                    status=ChangeRequestStatus.analysis,
                ),
            )

        change_request = create_change_request(
            session,
            ChangeRequestCreate(
                project_id=project.id,
                key="CR-1",
                title="Lifecycle change request",
                description="Exercise the workflow actions",
                severity=Severity.high,
            ),
        )

        with pytest.raises(ValueError):
            update_change_request(session, change_request.id, ChangeRequestUpdate(status=ChangeRequestStatus.analysis))

        submitted = submit_change_request_for_analysis(session, change_request.id, WorkflowActionPayload(actor="analyst", comment="Start analysis"))
        approved = approve_change_request(session, submitted.id, WorkflowActionPayload(actor="approver", comment="Looks good"))
        implemented = mark_change_request_implemented(session, approved.id, WorkflowActionPayload(actor="developer", comment="Delivered"))
        closed = close_change_request(session, implemented.id, WorkflowActionPayload(actor="owner", comment="Done"))
        reopened = reopen_change_request(session, closed.id, WorkflowActionPayload(actor="owner", comment="Needs revisit"))
        resubmitted = submit_change_request_for_analysis(session, reopened.id, WorkflowActionPayload(actor="analyst-2", comment="Re-analysis"))
        rejected = reject_change_request(session, resubmitted.id, WorkflowActionPayload(actor="approver-2", comment="Reject after review"))

        detail = get_change_request_detail(session, rejected.id)

        assert rejected.status == ChangeRequestStatus.rejected
        assert detail["change_request"].status == ChangeRequestStatus.rejected
        assert [event.action for event in detail["history"]] == [
            "submit_analysis",
            "approve",
            "implement",
            "close",
            "reopen",
            "submit_analysis",
            "reject",
        ]
        assert detail["history"][0].from_status == "open"
        assert detail["history"][-1].to_status == "rejected"


def test_configuration_context_compare_handles_empty_and_cross_project_inputs():
    with make_session() as session:
        project_a = create_project(session, ProjectCreate(code="P-FED-6", name="P-FED-6", description=""))
        project_b = create_project(session, ProjectCreate(code="P-FED-7", name="P-FED-7", description=""))
        left = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_a.id,
                key="CTX-A",
                name="Empty A",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )
        right = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_a.id,
                key="CTX-B",
                name="Empty B",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )
        foreign = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_b.id,
                key="CTX-X",
                name="Foreign context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )

        empty = compare_configuration_contexts(session, left.id, right.id)
        assert empty.summary.added == 0
        assert empty.summary.removed == 0
        assert empty.summary.version_changed == 0
        assert empty.groups == []

        with pytest.raises(ValueError, match="same project"):
            compare_configuration_contexts(session, left.id, foreign.id)


def test_baseline_compare_groups_added_removed_and_version_changes():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-6B", name="P-FED-6B", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-BASE",
                title="Baseline requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
                version=1,
            ),
        )
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-BASE",
                name="Baseline block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
                version=1,
            ),
        )
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(project_id=project.id, name="Cameo", connector_type=ConnectorType.sysml),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="SYSML-BASE",
                artifact_type=ExternalArtifactType.sysml_element,
                name="Baseline artifact",
            ),
        )
        version = create_external_artifact_version(
            session,
            artifact.id,
            ExternalArtifactVersionCreate(version_label="3.0", revision_label="R3"),
        )
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Baseline",
                description="Approved snapshot",
                requirement_ids=[requirement.id],
                block_ids=[block.id],
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-COMPARE",
                name="Compare context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        requirement_model = session.get(Requirement, requirement.id)
        assert requirement_model is not None
        requirement_model.version = 2
        session.add(requirement_model)
        session.commit()
        session.refresh(requirement_model)
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement_model.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_test_case,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=create_test_case(
                    session,
                    TestCaseCreate(
                        project_id=project.id,
                        key="TST-CTX",
                        title="Context test",
                        method=TestMethod.bench,
                        status=TestCaseStatus.approved,
                    ),
                ).id,
                internal_object_version=1,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version.id,
            ),
        )

        comparison = compare_baseline_to_configuration_context(session, baseline.id, context.id)

        assert comparison.baseline.id == baseline.id
        assert comparison.configuration_context.id == context.id
        assert comparison.summary.added == 2
        assert comparison.summary.removed == 1
        assert comparison.summary.version_changed == 1
        requirement_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_requirement)
        assert requirement_group.version_changed[0].left.object_version == 1
        assert requirement_group.version_changed[0].right.object_version == 2
        block_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_block)
        assert block_group.removed[0].label == "BLK-BASE - Baseline block"
        artifact_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.external_artifact_version)
        assert artifact_group.added[0].connector_name == "Cameo"
        assert artifact_group.added[0].artifact_name == "Baseline artifact"
        assert artifact_group.added[0].version_label == "3.0"


def test_baseline_compare_groups_added_removed_and_version_changes_between_baselines():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-6C", name="P-FED-6C", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-BASE-2",
                title="Baseline requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
                version=1,
            ),
        )
        requirement_model = session.exec(select(Requirement).where(Requirement.id == requirement.id)).one()
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-BASE-2",
                name="Baseline block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
                version=1,
            ),
        )
        test_case_one = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-BASE-1",
                title="Baseline test one",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        test_case_two = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-BASE-2",
                title="Baseline test two",
                method=TestMethod.field,
                status=TestCaseStatus.approved,
            ),
        )

        left_baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Left baseline",
                description="Approved snapshot",
                requirement_ids=[requirement.id],
                block_ids=[block.id],
                test_case_ids=[test_case_one.id],
            ),
        )

        requirement_model.version = 2
        session.add(requirement_model)
        session.commit()
        session.refresh(requirement_model)

        block_model = session.exec(select(Block).where(Block.id == block.id)).one()
        block_model.status = BlockStatus.obsolete
        session.add(block_model)
        session.commit()
        session.refresh(block_model)

        right_baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Right baseline",
                description="Approved snapshot",
                requirement_ids=[requirement.id],
                test_case_ids=[test_case_one.id, test_case_two.id],
            ),
        )

        comparison = compare_baselines(session, left_baseline.id, right_baseline.id)

        assert comparison.left_baseline.id == left_baseline.id
        assert comparison.right_baseline.id == right_baseline.id
        assert comparison.summary.added == 1
        assert comparison.summary.removed == 1
        assert comparison.summary.version_changed == 1
        requirement_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_requirement)
        assert requirement_group.version_changed[0].left.object_version == 1
        assert requirement_group.version_changed[0].right.object_version == 2
        block_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_block)
        assert block_group.removed[0].label == "BLK-BASE-2 - Baseline block"
        test_group = next(group for group in comparison.groups if group.item_kind == ConfigurationItemKind.internal_test_case)
        assert any(item.label == "TST-BASE-2 - Baseline test two" for item in test_group.added)


def test_configuration_context_immutability_blocks_edits_and_mapping_changes():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-10", name="P-FED-10", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-LOCK",
                title="Locked requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-LOCK",
                name="Mutable then frozen",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        mapping = create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )

        locked = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-REL",
                name="Released context",
                context_type=ConfigurationContextType.released,
                status=ConfigurationContextStatus.active,
            ),
        )

        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=create_external_artifact_version(
                    session,
                    create_external_artifact(
                        session,
                        ExternalArtifactCreate(
                            project_id=project.id,
                            external_id="ART-LOCK",
                            artifact_type=ExternalArtifactType.document,
                            name="Locked artifact",
                        ),
                    ).id,
                    ExternalArtifactVersionCreate(version_label="1"),
                ).id,
            ),
        )

        frozen = update_configuration_context(
            session,
            context.id,
            ConfigurationContextUpdate(status=ConfigurationContextStatus.frozen),
        )
        assert frozen.status == ConfigurationContextStatus.frozen

        with pytest.raises(ValueError, match="cannot be modified"):
            update_configuration_context(session, context.id, ConfigurationContextUpdate(name="Still locked"))

        with pytest.raises(ValueError, match="cannot be modified"):
            create_configuration_item_mapping(
                session,
                context.id,
                ConfigurationItemMappingCreate(
                    item_kind=ConfigurationItemKind.internal_requirement,
                    internal_object_type=FederatedInternalObjectType.requirement,
                    internal_object_id=requirement.id,
                    internal_object_version=requirement.version,
                ),
            )

        with pytest.raises(ValueError, match="cannot be modified"):
            delete_configuration_item_mapping(session, mapping.id)

        with pytest.raises(ValueError, match="cannot be modified"):
            update_configuration_context(session, locked.id, ConfigurationContextUpdate(name="Released lock"))


def test_configuration_context_obsolete_is_immutable():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-12", name="P-FED-12", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-OBS",
                title="Obsolete lock requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-OBS",
                name="Obsolete context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.obsolete,
            ),
        )

        with pytest.raises(ValueError, match="cannot be modified"):
            update_configuration_context(session, context.id, ConfigurationContextUpdate(name="Still obsolete"))

        with pytest.raises(ValueError, match="cannot be modified"):
            create_configuration_item_mapping(
                session,
                context.id,
                ConfigurationItemMappingCreate(
                    item_kind=ConfigurationItemKind.internal_requirement,
                    internal_object_type=FederatedInternalObjectType.requirement,
                    internal_object_id=requirement.id,
                    internal_object_version=requirement.version,
                ),
            )

        mutable_mapping = create_configuration_item_mapping(
            session,
            create_configuration_context(
                session,
                ConfigurationContextCreate(
                    project_id=project.id,
                    key="CTX-OBS-MUT",
                    name="Mutable context",
                    context_type=ConfigurationContextType.review_gate,
                    status=ConfigurationContextStatus.active,
                ),
            ).id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        mutable_context = session.get(ConfigurationContext, mutable_mapping.configuration_context_id)
        assert mutable_context is not None
        mutable_context.status = ConfigurationContextStatus.obsolete
        session.add(mutable_context)
        session.commit()
        session.refresh(mutable_context)

        with pytest.raises(ValueError, match="cannot be modified"):
            delete_configuration_item_mapping(session, mutable_mapping.id)


def test_baseline_and_configuration_context_bridge_the_same_approved_item_set():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-11", name="P-FED-11", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-BRIDGE",
                title="Bridge requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        block = create_block(
            session,
            BlockCreate(
                project_id=project.id,
                key="BLK-BRIDGE",
                name="Bridge block",
                block_kind=BlockKind.system,
                abstraction_level=AbstractionLevel.logical,
                status=BlockStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-BRIDGE",
                title="Bridge test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project.id,
                name="Bridge baseline",
                description="Baseline linked to a configuration context",
                requirement_ids=[requirement.id],
                block_ids=[block.id],
                test_case_ids=[test_case.id],
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-BRIDGE",
                name="Bridge context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_block,
                internal_object_type=FederatedInternalObjectType.block,
                internal_object_id=block.id,
                internal_object_version=block.version,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_test_case,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=test_case.id,
                internal_object_version=test_case.version,
            ),
        )

        baseline_detail = get_baseline_detail(session, baseline.id)
        context_detail = get_configuration_context_service(session, context.id)

        assert baseline_detail["related_configuration_contexts"]
        assert baseline_detail["related_configuration_contexts"][0].id == context.id
        assert context_detail["related_baselines"]
        assert context_detail["related_baselines"][0].id == baseline.id


def test_verification_evidence_links_requirements_and_test_cases_and_exports():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-EVID-1", name="P-EVID-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-EVID",
                title="Evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-EVID",
                title="Evidence test",
                method=TestMethod.simulation,
                status=TestCaseStatus.approved,
            ),
        )

        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Monte Carlo validation report",
                evidence_type=VerificationEvidenceType.simulation,
                summary="Simulation outputs matched the endurance target.",
                source_name="Simulink",
                source_reference="run-2026-04-03",
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        requirement_detail = get_requirement_detail(session, requirement.id)
        test_case_detail = get_test_case_detail(session, test_case.id)
        bundle = export_project_bundle(session, project.id)

        assert evidence.linked_objects
        assert evidence.linked_objects[0].object_id in {requirement.id, test_case.id}
        assert len(requirement_detail["verification_evidence"]) == 1
        assert len(test_case_detail["verification_evidence"]) == 1
        assert requirement_detail["verification_evidence"][0].id == evidence.id
        assert test_case_detail["verification_evidence"][0].id == evidence.id
        assert {obj.object_id for obj in requirement_detail["verification_evidence"][0].linked_objects} == {requirement.id, test_case.id}
        assert bundle["verification_evidence"]
        assert bundle["verification_evidence"][0]["id"] == str(evidence.id)


def test_simulation_verification_evidence_preserves_model_scenario_inputs_and_outputs():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-SIM-1", name="P-SIM-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-SIM",
                title="Simulation-backed requirement",
                category=RequirementCategory.environment,
                priority=Priority.medium,
                verification_method=VerificationMethod.analysis,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-SIM",
                title="Simulation test case",
                method=TestMethod.simulation,
                status=TestCaseStatus.approved,
            ),
        )

        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Thermal simulation result",
                evidence_type=VerificationEvidenceType.simulation,
                summary="Simulation confirmed the thermal envelope.",
                observed_at=datetime.now(timezone.utc),
                source_name="Simulink",
                source_reference="SIM-THERM-42",
                metadata_json={
                    "simulation": {
                        "model": "Endurance Model",
                        "scenario": "Thermal envelope validation",
                        "inputs": {"ambient_low_c": -6, "ambient_high_c": 41},
                        "outputs": {"pass": True, "margin_c": 1.0},
                    }
                },
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        requirement_detail = get_requirement_detail(session, requirement.id)
        test_case_detail = get_test_case_detail(session, test_case.id)
        bundle = export_project_bundle(session, project.id)

        assert evidence.evidence_type == VerificationEvidenceType.simulation
        assert evidence.metadata_json["simulation"]["model"] == "Endurance Model"
        assert evidence.metadata_json["simulation"]["scenario"] == "Thermal envelope validation"
        assert evidence.metadata_json["simulation"]["inputs"]["ambient_low_c"] == -6
        assert evidence.metadata_json["simulation"]["outputs"]["pass"] is True
        assert requirement_detail["verification_evidence"][0].metadata_json["simulation"]["model"] == "Endurance Model"
        assert test_case_detail["verification_evidence"][0].metadata_json["simulation"]["outputs"]["margin_c"] == 1.0
        assert bundle["verification_evidence"][0]["metadata_json"]["simulation"]["model"] == "Endurance Model"


def test_simulation_evidence_links_requirements_tests_and_verification_evidence_and_exports():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-SIM-2", name="P-SIM-2", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-SIM-2",
                title="Simulation evidence requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.analysis,
                status=RequirementStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-SIM-2",
                title="Simulation evidence test",
                method=TestMethod.simulation,
                status=TestCaseStatus.ready,
            ),
        )
        verification_evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Existing verification evidence",
                evidence_type=VerificationEvidenceType.simulation,
                summary="Legacy evidence that simulation can reference.",
                observed_at=datetime.now(timezone.utc),
                source_name="Simulink",
                source_reference="SIM-LEGACY-1",
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        evidence = create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Thermal simulation result",
                model_reference="Thermal Model",
                scenario_name="Envelope validation",
                input_summary="Ambient sweep across the flight envelope.",
                inputs_json={"ambient_low_c": -6, "ambient_high_c": 41},
                expected_behavior="Remain inside the thermal envelope.",
                observed_behavior="Remain inside the thermal envelope with margin.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL"},
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
                linked_verification_evidence_ids=[verification_evidence.id],
            ),
        )

        requirement_detail = get_requirement_detail(session, requirement.id)
        test_case_detail = get_test_case_detail(session, test_case.id)
        service_detail = get_simulation_evidence_service(session, evidence.id)
        bundle = export_project_bundle(session, project.id)

        assert service_detail.id == evidence.id
        assert service_detail.linked_objects
        assert any(item.object_type == "verification_evidence" for item in service_detail.linked_objects)
        assert requirement_detail["simulation_evidence"]
        assert requirement_detail["simulation_evidence"][0].id == evidence.id
        assert test_case_detail["simulation_evidence"]
        assert test_case_detail["simulation_evidence"][0].id == evidence.id
        assert bundle["simulation_evidence"]
        assert bundle["simulation_evidence"][0]["title"] == "Thermal simulation result"
        assert bundle["simulation_evidence_links"]

def test_fmi_placeholder_contract_links_simulation_evidence_and_exports():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FMI-1", name="P-FMI-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-FMI",
                title="FMI-backed requirement",
                category=RequirementCategory.environment,
                priority=Priority.medium,
                verification_method=VerificationMethod.analysis,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-FMI",
                title="FMI-backed test case",
                method=TestMethod.simulation,
                status=TestCaseStatus.approved,
            ),
        )
        contract = create_fmi_contract(
            session,
            FMIContractCreate(
                project_id=project.id,
                key="FMI-ENV-001",
                name="Environment simulation contract",
                description="Placeholder contract for an environment model.",
                model_identifier="SIM-FLIGHT-ENDURANCE",
                model_version="1.4",
                model_uri="federation://SIM-FLIGHT-ENDURANCE",
                adapter_profile="simulink-placeholder",
                metadata_json={"adapter_capability": "simulation_metadata"},
            ),
        )
        evidence = create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="FMI simulation result",
                model_reference="Environment Model",
                scenario_name="Thermal envelope validation",
                input_summary="Ambient sweep across the flight envelope.",
                inputs_json={"ambient_low_c": -6, "ambient_high_c": 41},
                expected_behavior="Remain inside the thermal envelope.",
                observed_behavior="Remain inside the thermal envelope with margin.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                fmi_contract_id=contract.id,
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL"},
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        contract_detail = get_fmi_contract_service(session, contract.id)
        listed_contracts = list_fmi_contracts(session, project.id)
        evidence_detail = get_simulation_evidence_service(session, evidence.id)
        bundle = export_project_bundle(session, project.id)

        assert contract_detail.fmi_contract.id == contract.id
        assert contract_detail.fmi_contract.linked_simulation_evidence_count == 1
        assert contract_detail.simulation_evidence[0].id == evidence.id
        assert listed_contracts[0].id == contract.id
        assert evidence_detail.fmi_contract_id == contract.id
        assert evidence_detail.fmi_contract_key == contract.key
        assert bundle["fmi_contracts"][0]["id"] == str(contract.id)
        assert bundle["simulation_evidence"][0]["fmi_contract_id"] == str(contract.id)


def test_operational_evidence_batches_link_requirements_and_verification_evidence_and_exports():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-OP-1", name="P-OP-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-OP",
                title="Operational evidence requirement",
                category=RequirementCategory.operations,
                priority=Priority.high,
                verification_method=VerificationMethod.demonstration,
                status=RequirementStatus.approved,
            ),
        )
        verification_evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Operational verification evidence",
                evidence_type=VerificationEvidenceType.telemetry,
                summary="Telemetry can be referenced by operational batches.",
                observed_at=datetime.now(timezone.utc),
                source_name="Telemetry hub",
                source_reference="OP-VER-1",
                linked_requirement_ids=[requirement.id],
            ),
        )

        batch = create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Endurance field evidence batch",
                source_name="Telemetry aggregator",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(minutes=22),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Aggregated field telemetry from the endurance mission.",
                aggregated_observations_json={"duration_minutes": 22, "battery_consumption_pct": 88},
                quality_status=OperationalEvidenceQualityStatus.warning,
                derived_metrics_json={"coverage_minutes": 22},
                metadata_json={"contract_reference": "OP-EVBATCH:1"},
                linked_requirement_ids=[requirement.id],
                linked_verification_evidence_ids=[verification_evidence.id],
            ),
        )

        requirement_detail = get_requirement_detail(session, requirement.id)
        listed = list_operational_evidence(
            session,
            project.id,
            internal_object_type=OperationalEvidenceLinkObjectType.requirement,
            internal_object_id=requirement.id,
        )
        by_verification = list_operational_evidence(
            session,
            project.id,
            internal_object_type=OperationalEvidenceLinkObjectType.verification_evidence,
            internal_object_id=verification_evidence.id,
        )
        detail = get_operational_evidence_service(session, batch.id)
        bundle = export_project_bundle(session, project.id)

        assert requirement_detail["operational_evidence"]
        assert requirement_detail["operational_evidence"][0].id == batch.id
        assert listed and listed[0].id == batch.id
        assert by_verification and by_verification[0].id == batch.id
        assert detail.id == batch.id
        assert {item.object_type for item in detail.linked_objects} == {"requirement", "verification_evidence"}
        assert bundle["operational_evidence"]
        assert bundle["operational_evidence"][0]["title"] == "Endurance field evidence batch"
        assert bundle["operational_evidence_links"]


def test_software_component_traceability_and_evidence_visibility():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-SW-1", name="P-SW-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-SW",
                title="Software shall publish mission telemetry",
                category=RequirementCategory.operations,
                priority=Priority.high,
                verification_method=VerificationMethod.demonstration,
            ),
        )
        component = create_component(
            session,
            ComponentCreate(
                project_id=project.id,
                key="CMP-SW",
                name="Flight Software",
                description="Autonomy and mission software",
                type=ComponentType.software_module,
                status=ComponentStatus.validated,
                version=3,
                metadata_json={"repository": "git@example.com:drone/flight.git", "entry_point": "src/main.py"},
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.requirement,
                source_id=requirement.id,
                target_type=LinkObjectType.component,
                target_id=component.id,
                relation_type=RelationType.allocated_to,
                rationale="Software realizes telemetry publishing.",
            ),
        )
        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Software runtime trace",
                evidence_type=VerificationEvidenceType.telemetry,
                summary="Runtime telemetry proves the software module is active.",
                observed_at=datetime.now(timezone.utc),
                source_name="Flight Software",
                source_reference="CMP-SW",
                metadata_json={"software": {"revision": "abc123"}},
                linked_component_ids=[component.id],
            ),
        )

        detail = get_component_detail(session, component.id)
        bundle = export_project_bundle(session, project.id)

        assert detail["component"].type == ComponentType.software_module
        assert detail["verification_evidence"][0].id == evidence.id
        assert detail["verification_evidence"][0].linked_objects[0].object_id == component.id
        assert any(link.target_id == component.id and link.relation_type == RelationType.allocated_to for link in detail["links"])
        assert any(item["key"] == "CMP-SW" for item in bundle["components"])
        assert any(item["title"] == "Software runtime trace" for item in bundle["verification_evidence"])


def test_non_conformity_entity_links_evidence_and_impacts():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-NC-1", name="P-NC-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-NC",
                title="Requirement affected by non-conformity",
                category=RequirementCategory.safety,
                priority=Priority.high,
                verification_method=VerificationMethod.analysis,
            ),
        )
        non_conformity = create_non_conformity(
            session,
            NonConformityCreate(
                project_id=project.id,
                key="NC-DET-1",
                title="Overheated enclosure detected",
                description="Thermal excursion observed during bench check.",
                status=NonConformityStatus.detected,
                disposition=NonConformityDisposition.rework,
                review_comment="Investigate thermal mitigation before closure.",
                severity=Severity.high,
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.non_conformity,
                source_id=non_conformity.id,
                target_type=LinkObjectType.requirement,
                target_id=requirement.id,
                relation_type=RelationType.impacts,
                rationale="Issue impacts the safety requirement.",
            ),
        )
        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Non-conformity inspection note",
                evidence_type=VerificationEvidenceType.inspection,
                summary="Inspection record closes the loop on the detected issue.",
                observed_at=datetime.now(timezone.utc),
                source_name="Quality Assurance",
                source_reference="NC-DET-1",
                linked_non_conformity_ids=[non_conformity.id],
            ),
        )

        detail = get_non_conformity_detail(session, non_conformity.id)
        updated = update_non_conformity(
            session,
            non_conformity.id,
            NonConformityUpdate(status=NonConformityStatus.contained, disposition=NonConformityDisposition.accept, review_comment="Accepted with mitigation."),
        )

        assert detail["non_conformity"].status == NonConformityStatus.detected
        assert detail["non_conformity"].disposition == NonConformityDisposition.rework
        assert detail["verification_evidence"][0].id == evidence.id
        assert detail["verification_evidence"][0].linked_objects[0].object_id == non_conformity.id
        assert detail["related_requirements"][0].object_id == requirement.id
        assert any(item.object_type == "requirement" for item in detail["impact_summary"])
        assert any(item.object_type == "requirement" for item in detail["impact"].likely_impacted)
        assert updated.status == NonConformityStatus.contained
        assert updated.disposition == NonConformityDisposition.accept
        snapshot = session.exec(select(RevisionSnapshot).where(RevisionSnapshot.object_type == "non_conformity", RevisionSnapshot.object_id == non_conformity.id)).all()
        assert snapshot and snapshot[0].snapshot_hash


def test_backend_coverage_spans_configuration_connectors_evidence_and_export():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-H2-1", name="P-H2-1", description=""))
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(project_id=project.id, name="DOORS NG", connector_type=ConnectorType.doors),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="REQ-H2-1",
                artifact_type=ExternalArtifactType.requirement,
                name="Coverage requirement",
                status=ExternalArtifactStatus.active,
            ),
        )
        version = create_external_artifact_version(
            session,
            artifact.id,
            ExternalArtifactVersionCreate(version_label="7.2", revision_label="R3"),
        )
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-H2-1",
                title="Coverage requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
                status=RequirementStatus.approved,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-H2-1",
                title="Coverage test",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CC-H2-1",
                name="Coverage context",
                status=ConfigurationContextStatus.active,
                context_type=ConfigurationContextType.working,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
                role_label="Tracked requirement",
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version.id,
                role_label="Authoritative requirement source",
            ),
        )
        non_conformity = create_non_conformity(
            session,
            NonConformityCreate(
                project_id=project.id,
                key="NC-H2-1",
                title="Coverage non-conformity",
                description="Regression note for coverage checks.",
                status=NonConformityStatus.detected,
                severity=Severity.medium,
            ),
        )
        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Coverage evidence",
                evidence_type=VerificationEvidenceType.test_result,
                summary="Verification evidence linked to the authored requirement and test case.",
                observed_at=datetime.now(timezone.utc),
                source_name="QA lab",
                source_reference="QA-H2-1",
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
                linked_non_conformity_ids=[non_conformity.id],
            ),
        )
        create_link(
            session,
            LinkCreate(
                project_id=project.id,
                source_type=LinkObjectType.non_conformity,
                source_id=non_conformity.id,
                target_type=LinkObjectType.requirement,
                target_id=requirement.id,
                relation_type=RelationType.impacts,
                rationale="Coverage issue impacts the requirement.",
            ),
        )

        registry = get_authoritative_registry_summary(session, project.id)
        context_detail = get_configuration_context_service(session, context.id)
        non_conformity_detail = get_non_conformity_detail(session, non_conformity.id)
        bundle = export_project_bundle(session, project.id)

        assert registry.connectors == 1
        assert registry.external_artifacts == 1
        assert registry.external_artifact_versions == 1
        assert context_detail["resolved_view"]["internal"]
        assert context_detail["resolved_view"]["external"]
        assert non_conformity_detail["verification_evidence"][0].id == evidence.id
        assert bundle["connectors"][0]["name"] == "DOORS NG"
        assert bundle["configuration_contexts"]
        assert bundle["configuration_item_mappings"]
        assert bundle["verification_evidence"]
        assert bundle["non_conformities"]

def test_json_import_creates_external_artifacts_and_verification_evidence():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-IMP-1", name="P-IMP-1", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-IMP-1",
                title="Imported requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-IMP-1",
                title="Imported test case",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )

        payload = ProjectImportCreate(
            format="json",
            content=json.dumps({
                "external_artifacts": [
                    {
                        "record_type": "external_artifact",
                        "external_id": "EXT-IMP-1",
                        "artifact_type": "document",
                        "name": "Imported document",
                        "description": "Imported external artifact",
                    }
                ],
                "verification_evidence": [
                    {
                        "record_type": "verification_evidence",
                        "title": "Imported verification evidence",
                        "evidence_type": "analysis",
                        "summary": "Imported evidence from JSON.",
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                        "source_name": "Import tool",
                        "source_reference": "IMP-JSON-1",
                        "linked_requirement_ids": [str(requirement.id)],
                        "linked_test_case_ids": [str(test_case.id)],
                    }
                ],
            }),
        )

        result = import_project_records(session, project.id, payload)
        bundle = export_project_bundle(session, project.id)

        assert result.summary.parsed_records == 2
        assert result.summary.created_external_artifacts == 1
        assert result.summary.created_verification_evidence == 1
        assert result.external_artifacts[0].external_id == "EXT-IMP-1"
        assert {item.object_id for item in result.verification_evidence[0].linked_objects} == {requirement.id, test_case.id}
        assert any(item["external_id"] == "EXT-IMP-1" for item in bundle["external_artifacts"])
        assert any(item["title"] == "Imported verification evidence" for item in bundle["verification_evidence"])
