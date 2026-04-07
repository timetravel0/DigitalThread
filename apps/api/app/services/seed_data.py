"""Seed service layer for the DigitalThread API."""

from __future__ import annotations

from collections import defaultdict, deque
from collections import Counter
import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlmodel import Session

from app.models import (
    AbstractionLevel,
    ApprovalActionLog,
    ArtifactLink,
    ArtifactLinkRelationType,
    Baseline,
    BaselineItem,
    BaselineObjectType,
    BaselineStatus,
    Block,
    BlockContainment,
    BlockContainmentRelationType,
    BlockKind,
    BlockStatus,
    ChangeImpact,
    ChangeRequest,
    ChangeRequestStatus,
    Component,
    ComponentStatus,
    ComponentType,
    ConfigurationContext,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConfigurationItemMapping,
    ConnectorDefinition,
    ConnectorType,
    ExternalArtifact,
    ExternalArtifactStatus,
    ExternalArtifactType,
    ExternalArtifactVersion,
    FMIContract,
    FederatedInternalObjectType,
    ImpactLevel,
    Link,
    LinkObjectType,
    NonConformity,
    NonConformityDisposition,
    NonConformityStatus,
    OperationalEvidence,
    OperationalEvidenceLink,
    OperationalEvidenceLinkObjectType,
    OperationalEvidenceQualityStatus,
    OperationalEvidenceSourceType,
    OperationalOutcome,
    OperationalRun,
    Priority,
    Project,
    ProjectStatus,
    RelationType,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    RequirementVerificationStatus,
    RevisionSnapshot,
    Severity,
    SimulationEvidence,
    SimulationEvidenceLink,
    SimulationEvidenceLinkObjectType,
    SimulationEvidenceResult,
    SysMLObjectType,
    SysMLRelation,
    SysMLRelationType,
    TestCase,
    TestCaseStatus,
    TestMethod,
    TestRun,
    TestRunResult,
    VerificationEvidence,
    VerificationEvidenceLink,
    VerificationEvidenceType,
    VerificationMethod,
    utcnow,
)
from app.schemas import (
    ApprovalActionLogRead,
    ArtifactLinkCreate,
    ArtifactLinkRead,
    AuthoritativeRegistrySummary,
    BaselineBridgeContextRead,
    BaselineComparisonResponse,
    BaselineContextComparisonResponse,
    BaselineCreate,
    BaselineDetailRead,
    BaselineItemRead,
    BaselineRead,
    BlockContainmentCreate,
    BlockContainmentRead,
    BlockCreate,
    BlockRead,
    BlockTreeNode,
    BlockUpdate,
    ChangeImpactCreate,
    ChangeImpactRead,
    ChangeRequestCreate,
    ChangeRequestDetail,
    ChangeRequestRead,
    ChangeRequestUpdate,
    ComponentCreate,
    ComponentDetail,
    ComponentRead,
    ComponentUpdate,
    ConfigurationContextComparisonChange,
    ConfigurationContextComparisonEntry,
    ConfigurationContextComparisonGroup,
    ConfigurationContextComparisonResponse,
    ConfigurationContextComparisonSummary,
    ConfigurationContextCreate,
    ConfigurationContextRead,
    ConfigurationContextUpdate,
    ConfigurationItemMappingCreate,
    ConfigurationItemMappingRead,
    ConnectorDefinitionCreate,
    ConnectorDefinitionRead,
    ConnectorDefinitionUpdate,
    DashboardKpis,
    DerivationRow,
    ExternalArtifactCreate,
    ExternalArtifactRead,
    ExternalArtifactUpdate,
    ExternalArtifactVersionCreate,
    ExternalArtifactVersionRead,
    FMIContractCreate,
    FMIContractDetail,
    FMIContractRead,
    GlobalDashboard,
    ImpactResponse,
    LinkCreate,
    LinkRead,
    MatrixCell,
    MatrixColumn,
    MatrixResponse,
    MatrixRow,
    NonConformityCreate,
    NonConformityDetail,
    NonConformityRead,
    NonConformityUpdate,
    ObjectSummary,
    OperationalEvidenceCreate,
    OperationalEvidenceLinkRead,
    OperationalEvidenceRead,
    OperationalRunCreate,
    OperationalRunDetail,
    OperationalRunRead,
    OperationalRunUpdate,
    ProjectCreate,
    ProjectDashboard,
    ProjectImportCreate,
    ProjectImportResponse,
    ProjectImportSummary,
    ProjectRead,
    ProjectTabStats,
    ProjectUpdate,
    RequirementCreate,
    RequirementDetail,
    RequirementRead,
    RequirementUpdate,
    RequirementVerificationEvaluation,
    ReviewQueueItem,
    ReviewQueueResponse,
    RevisionSnapshotRead,
    SatisfactionRow,
    STEPAP242ContractResponse,
    STEPAP242IdentifierRow,
    STEPAP242PartRow,
    STEPAP242RelationRow,
    STEPAP242Summary,
    SimulationEvidenceCreate,
    SimulationEvidenceLinkRead,
    SimulationEvidenceRead,
    SysMLBlockMappingRow,
    SysMLDerivationResponse,
    SysMLMappingContractResponse,
    SysMLMappingRelationRow,
    SysMLMappingSummary,
    SysMLRelationCreate,
    SysMLRelationRead,
    SysMLRequirementMappingRow,
    SysMLSatisfactionResponse,
    SysMLTreeResponse,
    SysMLVerificationResponse,
    TestCaseCreate,
    TestCaseDetail,
    TestCaseRead,
    TestCaseUpdate,
    TestRunCreate,
    TestRunRead,
    VerificationEvidenceCreate,
    VerificationEvidenceRead,
    VerificationRow,
    VerificationStatusBreakdown,
    WorkflowActionPayload,
)

OBJECT_MODELS = {
    "project": Project,
    "requirement": Requirement,
    "block": Block,
    "component": Component,
    "external_artifact": ExternalArtifact,
    "test_case": TestCase,
    "test_run": TestRun,
    "operational_run": OperationalRun,
    "simulation_evidence": SimulationEvidence,
    "fmi_contract": FMIContract,
    "operational_evidence": OperationalEvidence,
    "baseline": Baseline,
    "change_request": ChangeRequest,
    "non_conformity": NonConformity,
    "verification_evidence": VerificationEvidence,
}

from app.services._common import _add, _first_item, _snapshot, _touch, _seed_manufacturing_demo_details, _seed_personal_demo_details, _seed_profile_demo
from app.services.baseline_service import create_baseline
from app.services.configuration_service import list_configuration_item_mappings
from app.services.evidence_service import create_operational_evidence, create_simulation_evidence, create_verification_evidence
from app.services.link_service import create_sysml_relation



def seed_demo(session: Session) -> dict[str, Any]:
    project = _first_item(session.exec(select(Project).where(Project.code == "DRONE-001")))
    if project is None:
        project = _add(
            session,
            Project(
                code="DRONE-001",
                name="Inspection Drone MVP",
                description="Mission-driven drone demo that traces need -> design -> evidence -> change.",
                status=ProjectStatus.active,
            ),
        )

    reqs = {}
    for p in [
        {"project_id": project.id, "key": "DR-REQ-001", "title": "Drone shall fly for at least 30 minutes", "description": "Mission endurance target for the inspection route, with reserve for recovery.", "category": RequirementCategory.performance, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "verification_criteria_json": {"telemetry_thresholds": {"duration_minutes": {"min": 30}, "battery_consumption_pct": {"max": 85}}}, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-002", "title": "Drone shall stream real-time video to ground operator", "description": "Operator situational awareness requirement for the inspection mission.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-003", "title": "Drone shall operate between -5C and 40C", "description": "Environmental constraint derived from the intended mission profile.", "category": RequirementCategory.environment, "priority": Priority.high, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-REQ-004", "title": "Drone shall detect obstacles during low altitude flight", "description": "Safety requirement for the inspection route and landing approach.", "category": RequirementCategory.safety, "priority": Priority.critical, "verification_method": VerificationMethod.test, "status": RequirementStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-REQ-005", "title": "Drone shall support remote monitoring of battery and mission status", "description": "Ground-control visibility requirement for mission health and endurance.", "category": RequirementCategory.operations, "priority": Priority.high, "verification_method": VerificationMethod.demonstration, "status": RequirementStatus.draft, "version": 1, "verification_criteria_json": {"telemetry_thresholds": {"battery_consumption_pct": {"max": 85}}}},
        {"project_id": project.id, "key": "DR-REQ-006", "title": "Battery pack shall support mission reserve margin of 10 percent", "description": "Derived reserve requirement created from the endurance mission need.", "category": RequirementCategory.performance, "priority": Priority.medium, "verification_method": VerificationMethod.analysis, "status": RequirementStatus.draft, "version": 1, "parent_requirement_id": None},
    ]:
        item = _first_item(session.exec(select(Requirement).where(Requirement.project_id == project.id, Requirement.key == p["key"])))
        reqs[p["key"]] = item or _add(session, Requirement.model_validate(p))

    if reqs["DR-REQ-006"].parent_requirement_id is None:
        reqs["DR-REQ-006"].parent_requirement_id = reqs["DR-REQ-001"].id
        _touch(reqs["DR-REQ-006"])
        _add(session, reqs["DR-REQ-006"])

    for requirement in reqs.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "requirement", RevisionSnapshot.object_id == requirement.id)).first():
            _snapshot(session, "requirement", requirement, "Seeded requirement", "seed")

    blocks = {}
    for p in [
        {"project_id": project.id, "key": "DR-BLK-001", "name": "Drone System", "description": "Mission-level architecture for the inspection drone.", "block_kind": BlockKind.system, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-002", "name": "Power Subsystem", "description": "Logical power architecture for endurance and reserve management.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-003", "name": "Propulsion Subsystem", "description": "Logical lift and propulsion architecture for the mission profile.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.in_review, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-004", "name": "Battery Pack", "description": "Physical battery assembly selected to support endurance.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-005", "name": "Flight Controller", "description": "Physical controller coordinating flight, telemetry, and safety behavior.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
        {"project_id": project.id, "key": "DR-BLK-006", "name": "Camera Module", "description": "Physical inspection payload for live video evidence.", "block_kind": BlockKind.component, "abstraction_level": AbstractionLevel.physical, "status": BlockStatus.draft, "version": 1},
        {"project_id": project.id, "key": "DR-BLK-007", "name": "Obstacle Detection Subsystem", "description": "Logical sensing and avoidance architecture for low-altitude safety.", "block_kind": BlockKind.subsystem, "abstraction_level": AbstractionLevel.logical, "status": BlockStatus.approved, "version": 1, "approved_at": datetime.now(timezone.utc), "approved_by": "seed"},
    ]:
        item = _first_item(session.exec(select(Block).where(Block.project_id == project.id, Block.key == p["key"])))
        blocks[p["key"]] = item or _add(session, Block.model_validate(p))

    for block in blocks.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "block", RevisionSnapshot.object_id == block.id)).first():
            _snapshot(session, "block", block, "Seeded block", "seed")

    for parent, child in [
        ("DR-BLK-001", "DR-BLK-002"),
        ("DR-BLK-001", "DR-BLK-003"),
        ("DR-BLK-001", "DR-BLK-005"),
        ("DR-BLK-001", "DR-BLK-006"),
        ("DR-BLK-001", "DR-BLK-007"),
        ("DR-BLK-002", "DR-BLK-004"),
    ]:
        if not session.exec(select(BlockContainment).where(BlockContainment.project_id == project.id, BlockContainment.parent_block_id == blocks[parent].id, BlockContainment.child_block_id == blocks[child].id)).first():
            _add(session, BlockContainment(project_id=project.id, parent_block_id=blocks[parent].id, child_block_id=blocks[child].id, relation_type=BlockContainmentRelationType.contains))

    comps = {}
    for p in [
        {"project_id": project.id, "key": "DR-CMP-001", "name": "Li-Ion Battery Pack", "description": "Physical battery pack sized for the endurance target.", "type": ComponentType.battery, "part_number": "BAT-3000", "supplier": "VoltCraft", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"capacity_mah": 12000}},
        {"project_id": project.id, "key": "DR-CMP-002", "name": "Brushless Motor Set", "description": "Physical lift motors used in the propulsion chain.", "type": ComponentType.motor, "part_number": "MTR-2208", "supplier": "AeroSpin", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"kv": 920}},
        {"project_id": project.id, "key": "DR-CMP-003", "name": "Flight Controller", "description": "Physical controller implementing mission behavior and telemetry.", "type": ComponentType.flight_controller, "part_number": "FC-REV2", "supplier": "SkyLogic", "status": ComponentStatus.validated, "version": 2, "metadata_json": {"firmware": "1.4.3"}},
        {"project_id": project.id, "key": "DR-CMP-004", "name": "Camera Module", "description": "Physical payload for the inspection video stream.", "type": ComponentType.camera, "part_number": "CAM-1080P", "supplier": "OptiView", "status": ComponentStatus.validated, "version": 1, "metadata_json": {"resolution": "1080p"}},
        {"project_id": project.id, "key": "DR-CMP-005", "name": "Obstacle Sensor", "description": "Physical sensing hardware for low-altitude obstacle detection.", "type": ComponentType.sensor, "part_number": "OBS-LIDAR-1", "supplier": "SenseWorks", "status": ComponentStatus.selected, "version": 1, "metadata_json": {"range_m": 18}},
        {"project_id": project.id, "key": "DR-CMP-006", "name": "Flight Software", "description": "Software realization of autonomy, telemetry, and control.", "type": ComponentType.software_module, "part_number": "SW-FLT-1", "supplier": "ThreadLite Labs", "status": ComponentStatus.validated, "version": 3, "metadata_json": {"repository": "git@example.com:drone/flight.git", "branch": "main", "entry_point": "src/autonomy/main.py"}},
    ]:
        item = _first_item(session.exec(select(Component).where(Component.project_id == project.id, Component.key == p["key"])))
        comps[p["key"]] = item or _add(session, Component.model_validate(p))

    tests = {}
    for p in [
        {"project_id": project.id, "key": "DR-TST-001", "title": "Flight Endurance Test", "description": "Verification step for the mission endurance target.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-002", "title": "Video Streaming Test", "description": "Verification step for operator video awareness.", "method": TestMethod.bench, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-003", "title": "Temperature Envelope Test", "description": "Simulation-based verification of environmental limits.", "method": TestMethod.simulation, "status": TestCaseStatus.ready, "version": 1},
        {"project_id": project.id, "key": "DR-TST-004", "title": "Obstacle Detection Test", "description": "Verification step for low-altitude safety behavior.", "method": TestMethod.field, "status": TestCaseStatus.ready, "version": 1},
    ]:
        item = _first_item(session.exec(select(TestCase).where(TestCase.project_id == project.id, TestCase.key == p["key"])))
        tests[p["key"]] = item or _add(session, TestCase.model_validate(p))

    for test_case in tests.values():
        if not session.exec(select(RevisionSnapshot).where(RevisionSnapshot.project_id == project.id, RevisionSnapshot.object_type == "test_case", RevisionSnapshot.object_id == test_case.id)).first():
            _snapshot(session, "test_case", test_case, "Seeded test case", "seed")

    if tests["DR-TST-001"].status != TestCaseStatus.approved:
        tests["DR-TST-001"].status = TestCaseStatus.approved
        tests["DR-TST-001"].approved_at = datetime.now(timezone.utc)
        tests["DR-TST-001"].approved_by = "seed"
        _touch(tests["DR-TST-001"])
        _add(session, tests["DR-TST-001"])
        _snapshot(session, "test_case", tests["DR-TST-001"], "Approved endurance test for federation seed", "seed")

    for rel in [
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery contributes to endurance."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.satisfy, rationale="Flight controller manages video."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-006"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.satisfy, rationale="Camera module provides streaming."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery supports temperature envelope."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.satisfy, rationale="Controller monitors thermal state."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-007"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-004"].id, relation_type=SysMLRelationType.satisfy, rationale="Obstacle subsystem satisfies detection."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-005"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-005"].id, relation_type=SysMLRelationType.satisfy, rationale="Controller supports mission monitoring."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.block, source_id=blocks["DR-BLK-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-005"].id, relation_type=SysMLRelationType.satisfy, rationale="Battery status reported remotely."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-001"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.verify, rationale="Endurance verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-002"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-002"].id, relation_type=SysMLRelationType.verify, rationale="Streaming verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-003"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=SysMLRelationType.verify, rationale="Temperature verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.test_case, source_id=tests["DR-TST-004"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-004"].id, relation_type=SysMLRelationType.verify, rationale="Obstacle detection verification."),
        SysMLRelationCreate(project_id=project.id, source_type=SysMLObjectType.requirement, source_id=reqs["DR-REQ-006"].id, target_type=SysMLObjectType.requirement, target_id=reqs["DR-REQ-001"].id, relation_type=SysMLRelationType.deriveReqt, rationale="Reserve margin derived from endurance."),
    ]:
        if not session.exec(select(SysMLRelation).where(SysMLRelation.project_id == project.id, SysMLRelation.source_type == rel.source_type, SysMLRelation.source_id == rel.source_id, SysMLRelation.target_type == rel.target_type, SysMLRelation.target_id == rel.target_id, SysMLRelation.relation_type == rel.relation_type)).first():
            create_sysml_relation(session, rel)

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
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-006"].id, relation_type=RelationType.allocated_to, rationale="Flight software implements the video pipeline."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-005"].id, target_type=LinkObjectType.component, target_id=comps["DR-CMP-006"].id, relation_type=RelationType.allocated_to, rationale="Flight software publishes mission telemetry."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-001"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-001"].id, relation_type=RelationType.verifies, rationale="Endurance test verifies endurance."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-002"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-002"].id, relation_type=RelationType.verifies, rationale="Streaming test verifies video."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-003"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-003"].id, relation_type=RelationType.verifies, rationale="Temperature test verifies envelope."),
        LinkCreate(project_id=project.id, source_type=LinkObjectType.requirement, source_id=reqs["DR-REQ-004"].id, target_type=LinkObjectType.test_case, target_id=tests["DR-TST-004"].id, relation_type=RelationType.verifies, rationale="Obstacle test verifies obstacle detection."),
    ]:
        if not session.exec(select(Link).where(Link.project_id == project.id, Link.source_type == p.source_type, Link.source_id == p.source_id, Link.target_type == p.target_type, Link.target_id == p.target_id, Link.relation_type == p.relation_type)).first():
            _add(session, Link.model_validate(p))

    for p in [
        {
            "title": "Endurance verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Flight endurance evidence showing the mission falls short of the 30 minute target.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-001",
            "linked_requirement_ids": [reqs["DR-REQ-001"].id],
            "linked_test_case_ids": [tests["DR-TST-001"].id],
        },
        {
            "title": "Streaming verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Video stream evidence showing the operator view is available during the mission.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-002",
            "linked_requirement_ids": [reqs["DR-REQ-002"].id],
            "linked_test_case_ids": [tests["DR-TST-002"].id],
        },
        {
            "title": "Thermal simulation evidence",
            "evidence_type": VerificationEvidenceType.simulation,
            "summary": "Thermal simulation evidence showing the environment remains inside the declared envelope.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "Simulink Verification Export",
            "source_reference": "SIM-THERM-001",
            "linked_requirement_ids": [reqs["DR-REQ-003"].id],
            "linked_test_case_ids": [tests["DR-TST-003"].id],
            "metadata_json": {
                "simulation": {
                    "model": "Endurance Model",
                    "scenario": "Thermal envelope validation",
                    "inputs": {"ambient_low_c": -6, "ambient_high_c": 41},
                    "outputs": {"pass": True, "margin_c": 1.0},
                }
            },
        },
        {
            "title": "Obstacle verification evidence",
            "evidence_type": VerificationEvidenceType.test_result,
            "summary": "Obstacle verification evidence showing low-altitude safety checks are in place.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "QA Lab",
            "source_reference": "DR-TST-004",
            "linked_requirement_ids": [reqs["DR-REQ-004"].id],
            "linked_test_case_ids": [tests["DR-TST-004"].id],
        },
        {
            "title": "Flight software runtime evidence",
            "evidence_type": VerificationEvidenceType.telemetry,
            "summary": "Software telemetry evidence confirming the mission-control pipeline is active.",
            "observed_at": datetime.now(timezone.utc),
            "source_name": "Flight Software",
            "source_reference": "DR-CMP-006",
            "metadata_json": {"software": {"repository": "git@example.com:drone/flight.git", "revision": "a1b2c3d", "runtime": "autonomy"}},
            "linked_requirement_ids": [],
            "linked_test_case_ids": [],
            "linked_component_ids": [comps["DR-CMP-006"].id],
        },
    ]:
        if not session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project.id, VerificationEvidence.title == p["title"])).first():
            create_verification_evidence(
                session,
                VerificationEvidenceCreate(
                    project_id=project.id,
                    title=p["title"],
                    evidence_type=p["evidence_type"],
                    summary=p["summary"],
                    observed_at=p["observed_at"],
                    source_name=p["source_name"],
                    source_reference=p["source_reference"],
                    metadata_json=p.get("metadata_json", {}),
                    linked_requirement_ids=p["linked_requirement_ids"],
                linked_test_case_ids=p["linked_test_case_ids"],
                linked_component_ids=p.get("linked_component_ids", []),
            ),
        )

    thermal_verification_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Thermal simulation evidence",
            )
        )
    )
    endurance_verification_evidence = _first_item(
        session.exec(
            select(VerificationEvidence).where(
                VerificationEvidence.project_id == project.id,
                VerificationEvidence.title == "Endurance verification evidence",
            )
        )
    )
    fmi_contract = _first_item(
        session.exec(
            select(FMIContract).where(
                FMIContract.project_id == project.id,
                FMIContract.key == "FMI-THERMAL-001",
            )
        )
    )
    if fmi_contract is None:
        fmi_contract = _add(
            session,
            FMIContract(
                project_id=project.id,
                key="FMI-THERMAL-001",
                name="Thermal Envelope FMI Placeholder",
                description="Placeholder FMI-style contract for the endurance simulation model used in the mission narrative.",
                model_identifier="SIM-FLIGHT-ENDURANCE",
                model_version="1.4",
                model_uri="federation://SIM-FLIGHT-ENDURANCE",
                adapter_profile="simulink-placeholder",
                contract_version="fmi.placeholder.v1",
                metadata_json={"seeded": True, "adapter_capability": "simulation_metadata"},
            ),
        )
    if not session.exec(
        select(SimulationEvidence).where(
            SimulationEvidence.project_id == project.id,
            SimulationEvidence.title == "Thermal simulation result",
        )
    ).first():
        create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Thermal simulation result",
                model_reference="Endurance Model",
                scenario_name="Thermal envelope validation",
                input_summary="Ambient temperature sweep from -6C to 41C.",
                inputs_json={"ambient_low_c": -6, "ambient_high_c": 41},
                expected_behavior="Maintain thermal envelope and preserve margin.",
                observed_behavior="Simulation maintained the thermal envelope with 1.0C margin.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                fmi_contract_id=fmi_contract.id,
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL-ENVELOPE"},
                linked_requirement_ids=[reqs["DR-REQ-003"].id],
                linked_test_case_ids=[tests["DR-TST-003"].id],
                linked_verification_evidence_ids=[thermal_verification_evidence.id] if thermal_verification_evidence else [],
            ),
        )

    if not session.exec(
        select(OperationalEvidence).where(
            OperationalEvidence.project_id == project.id,
            OperationalEvidence.title == "Endurance field evidence batch",
        )
    ).first():
        create_operational_evidence(
            session,
            OperationalEvidenceCreate(
                project_id=project.id,
                title="Endurance field evidence batch",
                source_name="Telemetry aggregator",
                source_type=OperationalEvidenceSourceType.system,
                captured_at=datetime.now(timezone.utc),
                coverage_window_start=datetime.now(timezone.utc) - timedelta(minutes=22),
                coverage_window_end=datetime.now(timezone.utc),
                observations_summary="Aggregated field telemetry from the endurance mission and the resulting change trigger.",
                aggregated_observations_json={
                    "duration_minutes": 22,
                    "battery_consumption_pct": 88,
                    "altitude_m": 43,
                    "return_to_home": True,
                },
                quality_status=OperationalEvidenceQualityStatus.warning,
                derived_metrics_json={
                    "coverage_minutes": 22,
                    "low_battery_warning": True,
                },
                metadata_json={"contract_reference": "OP-EVBATCH:DR-RUN-001"},
                linked_requirement_ids=[reqs["DR-REQ-001"].id, reqs["DR-REQ-005"].id],
                linked_verification_evidence_ids=[endurance_verification_evidence.id] if endurance_verification_evidence else [],
            ),
        )

    run = _first_item(session.exec(select(OperationalRun).where(OperationalRun.project_id == project.id, OperationalRun.key == "DR-RUN-001")))
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

    cr = _first_item(session.exec(select(ChangeRequest).where(ChangeRequest.project_id == project.id, ChangeRequest.key == "CR-001")))
    if cr is None:
        cr = _add(session, ChangeRequest(project_id=project.id, key="CR-001", title="Increase battery endurance to support 35 minutes target", description="Change request raised after endurance evidence showed the mission stops short of the target. Investigate battery and propulsion changes to close the gap.", status=ChangeRequestStatus.open, severity=Severity.high))
    if not session.exec(select(ChangeImpact).where(ChangeImpact.change_request_id == cr.id)).first():
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-001"].id, impact_level=ImpactLevel.high, notes="Battery pack is the primary design driver behind the endurance gap."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="component", object_id=comps["DR-CMP-002"].id, impact_level=ImpactLevel.medium, notes="Motors affect power draw and endurance margin."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="requirement", object_id=reqs["DR-REQ-001"].id, impact_level=ImpactLevel.high, notes="Mission endurance requirement needs revision or decomposition."))
        _add(session, ChangeImpact(change_request_id=cr.id, object_type="test_case", object_id=tests["DR-TST-001"].id, impact_level=ImpactLevel.medium, notes="Endurance verification test likely changes as the design is updated."))

    nc = _first_item(session.exec(select(NonConformity).where(NonConformity.project_id == project.id, NonConformity.key == "NC-001")))
    if nc is None:
        nc = _add(
            session,
            NonConformity(
                project_id=project.id,
                key="NC-001",
                title="Battery pack overheating during endurance run",
                description="Observed battery thermal excursion above nominal limits.",
                status=NonConformityStatus.analyzing,
                disposition=NonConformityDisposition.rework,
                review_comment="Investigate thermal mitigation before closing the deviation.",
                severity=Severity.high,
            ),
        )
    if not session.exec(
        select(Link).where(
            Link.project_id == project.id,
            Link.source_type == LinkObjectType.non_conformity,
            Link.source_id == nc.id,
            Link.target_type == LinkObjectType.requirement,
            Link.target_id == reqs["DR-REQ-003"].id,
            Link.relation_type == RelationType.impacts,
        )
    ).first():
        _add(session, Link(project_id=project.id, source_type=LinkObjectType.non_conformity, source_id=nc.id, target_type=LinkObjectType.requirement, target_id=reqs["DR-REQ-003"].id, relation_type=RelationType.impacts, rationale="Thermal excursion impacts the environmental requirement."))
    if not session.exec(select(VerificationEvidence).where(VerificationEvidence.project_id == project.id, VerificationEvidence.title == "Non-conformity thermal observation")).first():
        create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Non-conformity thermal observation",
                evidence_type=VerificationEvidenceType.inspection,
                summary="Inspection record documenting the overheating issue.",
                observed_at=datetime.now(timezone.utc),
                source_name="Quality Engineering",
                source_reference="NC-001",
                linked_non_conformity_ids=[nc.id],
            ),
        )

    baseline = _first_item(session.exec(select(Baseline).where(Baseline.project_id == project.id, Baseline.name == "Initial Drone Baseline")))
    if baseline is None:
        create_baseline(session, BaselineCreate(project_id=project.id, name="Initial Drone Baseline", description="Baseline for the seeded drone MVP."))

    connectors = {}
    for p in [
        {"name": "DOORS NG", "connector_type": ConnectorType.doors, "base_url": "https://doors.example.local", "description": "Requirement source system."},
        {"name": "Cameo MBSE", "connector_type": ConnectorType.sysml, "base_url": "https://cameo.example.local", "description": "SysML model source."},
        {"name": "Teamcenter PLM", "connector_type": ConnectorType.plm, "base_url": "https://teamcenter.example.local", "description": "Physical part source."},
        {"name": "Simulink Verification Export", "connector_type": ConnectorType.simulation, "base_url": "https://simulink.example.local", "description": "Simulation evidence export."},
    ]:
        connector = _first_item(session.exec(select(ConnectorDefinition).where(ConnectorDefinition.project_id == project.id, ConnectorDefinition.name == p["name"])))
        connectors[p["name"]] = connector or _add(session, ConnectorDefinition(project_id=project.id, name=p["name"], connector_type=p["connector_type"], base_url=p["base_url"], description=p["description"], is_active=True, metadata_json={"seeded": True}))

    artifacts = {}
    for p in [
        {"external_id": "REQ-DOORS-001", "artifact_type": ExternalArtifactType.requirement, "name": "Endurance requirement", "description": "Authoritative DOORS requirement for mission endurance.", "connector": "DOORS NG", "canonical_uri": "doors://REQ-DOORS-001", "native_tool_url": "https://doors.example.local/objects/REQ-DOORS-001"},
        {"external_id": "SYSML-BLOCK-BATTERY", "artifact_type": ExternalArtifactType.sysml_element, "name": "Battery Pack", "description": "Authoritative Cameo block for the battery assembly.", "connector": "Cameo MBSE", "canonical_uri": "sysml://SYSML-BLOCK-BATTERY", "native_tool_url": "https://cameo.example.local/elements/SYSML-BLOCK-BATTERY"},
        {"external_id": "PLM-PART-DR-BATT-01", "artifact_type": ExternalArtifactType.cad_part, "name": "Battery Pack Assembly", "description": "Authoritative Teamcenter part for the battery assembly.", "connector": "Teamcenter PLM", "canonical_uri": "plm://PLM-PART-DR-BATT-01", "native_tool_url": "https://teamcenter.example.local/items/PLM-PART-DR-BATT-01"},
        {"external_id": "SIM-FLIGHT-ENDURANCE", "artifact_type": ExternalArtifactType.simulation_model, "name": "Endurance Model", "description": "Simulink model used to validate endurance behavior.", "connector": "Simulink Verification Export", "canonical_uri": "federation://SIM-FLIGHT-ENDURANCE", "native_tool_url": "https://simulink.example.local/models/SIM-FLIGHT-ENDURANCE"},
    ]:
        artifact = _first_item(session.exec(select(ExternalArtifact).where(ExternalArtifact.project_id == project.id, ExternalArtifact.external_id == p["external_id"])))
        artifacts[p["external_id"]] = artifact or _add(
            session,
            ExternalArtifact(
                project_id=project.id,
                connector_definition_id=connectors[p["connector"]].id,
                external_id=p["external_id"],
                artifact_type=p["artifact_type"],
                name=p["name"],
                description=p["description"],
                canonical_uri=p["canonical_uri"],
                native_tool_url=p["native_tool_url"],
                status=ExternalArtifactStatus.active,
                metadata_json={"seeded": True},
            ),
        )

    versions = {}
    for p in [
        {"artifact": "REQ-DOORS-001", "version_label": "7", "revision_label": "7", "metadata_json": {"owner": "systems"}},
        {"artifact": "SYSML-BLOCK-BATTERY", "version_label": "2", "revision_label": "2", "metadata_json": {"model_package": "drone-architecture"}},
        {"artifact": "PLM-PART-DR-BATT-01", "version_label": "C", "revision_label": "C", "metadata_json": {"supplier": "VoltCraft"}},
        {"artifact": "SIM-FLIGHT-ENDURANCE", "version_label": "1.4", "revision_label": "1.4", "metadata_json": {"solver": "Simulink"}},
    ]:
        artifact = artifacts[p["artifact"]]
        version = _first_item(session.exec(select(ExternalArtifactVersion).where(ExternalArtifactVersion.external_artifact_id == artifact.id, ExternalArtifactVersion.version_label == p["version_label"], ExternalArtifactVersion.revision_label == p["revision_label"])))
        versions[f'{p["artifact"]}:{p["version_label"]}'] = version or _add(
            session,
            ExternalArtifactVersion(
                external_artifact_id=artifact.id,
                version_label=p["version_label"],
                revision_label=p["revision_label"],
                checksum_or_signature=f"seed-{p['artifact']}-{p['version_label']}",
                effective_date=date.today(),
                source_timestamp=datetime.now(timezone.utc),
                metadata_json=p["metadata_json"],
            ),
        )

    for p in [
        {"internal_object_type": FederatedInternalObjectType.requirement, "internal_object_id": reqs["DR-REQ-001"].id, "external_artifact_id": artifacts["REQ-DOORS-001"].id, "external_artifact_version_id": versions["REQ-DOORS-001:7"].id, "relation_type": ArtifactLinkRelationType.maps_to, "rationale": "DR-REQ-001 maps to the authoritative DOORS requirement."},
        {"internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "external_artifact_id": artifacts["SYSML-BLOCK-BATTERY"].id, "external_artifact_version_id": versions["SYSML-BLOCK-BATTERY:2"].id, "relation_type": ArtifactLinkRelationType.maps_to, "rationale": "Battery Pack maps to the authoritative Cameo element."},
        {"internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "external_artifact_id": artifacts["PLM-PART-DR-BATT-01"].id, "external_artifact_version_id": versions["PLM-PART-DR-BATT-01:C"].id, "relation_type": ArtifactLinkRelationType.authoritative_reference, "rationale": "Battery Pack is referenced by the Teamcenter part."},
        {"internal_object_type": FederatedInternalObjectType.test_case, "internal_object_id": tests["DR-TST-001"].id, "external_artifact_id": artifacts["SIM-FLIGHT-ENDURANCE"].id, "external_artifact_version_id": versions["SIM-FLIGHT-ENDURANCE:1.4"].id, "relation_type": ArtifactLinkRelationType.validated_against, "rationale": "Endurance test validated against the simulation model."},
    ]:
        if not session.exec(
            select(ArtifactLink).where(
                ArtifactLink.project_id == project.id,
                ArtifactLink.internal_object_type == p["internal_object_type"],
                ArtifactLink.internal_object_id == p["internal_object_id"],
                ArtifactLink.external_artifact_id == p["external_artifact_id"],
                ArtifactLink.relation_type == p["relation_type"],
            )
        ).first():
            _add(
                session,
                ArtifactLink(
                    project_id=project.id,
                    internal_object_type=p["internal_object_type"],
                    internal_object_id=p["internal_object_id"],
                    external_artifact_id=p["external_artifact_id"],
                    external_artifact_version_id=p["external_artifact_version_id"],
                    relation_type=p["relation_type"],
                    rationale=p["rationale"],
                ),
            )

    context = _first_item(session.exec(select(ConfigurationContext).where(ConfigurationContext.project_id == project.id, ConfigurationContext.key == "DRN-PDR-0.3")))
    if context is None:
        context = _add(
            session,
            ConfigurationContext(
                project_id=project.id,
                key="DRN-PDR-0.3",
                name="Preliminary Design Review 0.3",
                description="Federated configuration snapshot for the seeded drone demo.",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )

    existing_mapping_ids = {
        (mapping.item_kind.value, mapping.internal_object_type.value if mapping.internal_object_type else None, str(mapping.internal_object_id) if mapping.internal_object_id else None, str(mapping.external_artifact_version_id) if mapping.external_artifact_version_id else None)
        for mapping in list_configuration_item_mappings(session, context.id)
    }
    for p in [
        {"item_kind": ConfigurationItemKind.internal_requirement, "internal_object_type": FederatedInternalObjectType.requirement, "internal_object_id": reqs["DR-REQ-001"].id, "internal_object_version": reqs["DR-REQ-001"].version, "role_label": "Approved requirement"},
        {"item_kind": ConfigurationItemKind.internal_block, "internal_object_type": FederatedInternalObjectType.block, "internal_object_id": blocks["DR-BLK-004"].id, "internal_object_version": blocks["DR-BLK-004"].version, "role_label": "Approved block"},
        {"item_kind": ConfigurationItemKind.internal_test_case, "internal_object_type": FederatedInternalObjectType.test_case, "internal_object_id": tests["DR-TST-001"].id, "internal_object_version": tests["DR-TST-001"].version, "role_label": "Approved test case"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["REQ-DOORS-001:7"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["SYSML-BLOCK-BATTERY:2"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["PLM-PART-DR-BATT-01:C"].id, "role_label": "Authoritative external reference"},
        {"item_kind": ConfigurationItemKind.external_artifact_version, "external_artifact_version_id": versions["SIM-FLIGHT-ENDURANCE:1.4"].id, "role_label": "Authoritative external reference"},
    ]:
        key = (
            p["item_kind"].value,
            p.get("internal_object_type").value if p.get("internal_object_type") else None,
            str(p.get("internal_object_id")) if p.get("internal_object_id") else None,
            str(p.get("external_artifact_version_id")) if p.get("external_artifact_version_id") else None,
        )
        if key not in existing_mapping_ids:
            _add(
                session,
                ConfigurationItemMapping(
                    configuration_context_id=context.id,
                    item_kind=p["item_kind"],
                    internal_object_type=p.get("internal_object_type"),
                    internal_object_id=p.get("internal_object_id"),
                    internal_object_version=p.get("internal_object_version"),
                    external_artifact_version_id=p.get("external_artifact_version_id"),
                    role_label=p.get("role_label"),
                    notes=p.get("notes"),
                ),
            )

    return {"project_id": str(project.id), "seeded": True}

def seed_manufacturing_demo(session: Session) -> dict[str, Any]:
    base = _seed_profile_demo(
        session,
        code="MFG-001",
        name="Production Line Demo",
        description="Manufacturing demo that traces specifications to components, quality checks, evidence, and change.",
        profile="manufacturing",
        requirement_key="MFG-SPEC-001",
        requirement_title="Line shall maintain 99.5 percent fill accuracy",
        requirement_description="Quality specification for the production line's filled package accuracy and reject control.",
        requirement_category=RequirementCategory.performance,
        requirement_priority=Priority.critical,
        requirement_verification_method=VerificationMethod.test,
        block_key="MFG-BLK-001",
        block_name="Packaging Line",
        block_description="Top-level production line architecture for fill, inspect, and reject flow.",
        block_kind=BlockKind.system,
        block_abstraction_level=AbstractionLevel.logical,
        component_key="MFG-CMP-001",
        component_name="Fill Head Assembly",
        component_description="Physical fill head used to realize the accuracy target.",
        component_type=ComponentType.other,
        component_part_number="MFG-FILL-HEAD-01",
        component_supplier="PackRight",
        test_key="MFG-QC-001",
        test_title="Fill Accuracy Check",
        test_description="Quality check that validates production fill accuracy against specification.",
        test_method=TestMethod.inspection,
    )
    _seed_manufacturing_demo_details(session, UUID(base["project_id"]), base)
    return base

def seed_personal_demo(session: Session) -> dict[str, Any]:
    base = _seed_profile_demo(
        session,
        code="HOME-001",
        name="Home Infrastructure Demo",
        description="Personal demo that traces a goal to elements, evidence, and change.",
        profile="personal",
        requirement_key="HOME-GOAL-001",
        requirement_title="Home network shall keep backups available overnight",
        requirement_description="Personal goal for keeping backup copies online through the night and ready to restore.",
        requirement_category=RequirementCategory.performance,
        requirement_priority=Priority.high,
        requirement_verification_method=VerificationMethod.test,
        block_key="HOME-BLK-001",
        block_name="Home Network System",
        block_description="Top-level home network architecture supporting backup and isolation behavior.",
        block_kind=BlockKind.system,
        block_abstraction_level=AbstractionLevel.logical,
        component_key="HOME-CMP-001",
        component_name="Backup Storage Node",
        component_description="Home storage element used to realize the backup availability goal.",
        component_type=ComponentType.other,
        component_part_number="HOME-NAS-01",
        component_supplier="SyncedHome",
        test_key="HOME-VER-001",
        test_title="Overnight Backup Check",
        test_description="Verification check that the storage node remains reachable overnight.",
        test_method=TestMethod.inspection,
    )
    _seed_personal_demo_details(session, UUID(base["project_id"]), base)
    return base
