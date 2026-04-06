from datetime import date, datetime, timedelta, timezone
import csv
import io

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    ArtifactLinkRelationType,
    Block,
    BlockContainmentRelationType,
    BlockKind,
    AbstractionLevel,
    BlockStatus,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConfigurationItemMapping,
    ConnectorDefinition,
    ConnectorType,
    Component,
    ComponentStatus,
    ComponentType,
    ExternalArtifact,
    ExternalArtifactStatus,
    ExternalArtifactType,
    FederatedInternalObjectType,
    OperationalEvidence,
    OperationalEvidenceLinkObjectType,
    OperationalEvidenceQualityStatus,
    OperationalEvidenceSourceType,
    Priority,
    Project,
    SimulationEvidenceLinkObjectType,
    SimulationEvidenceResult,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    SysMLObjectType,
    SysMLRelationType,
    TestCase,
    TestCaseStatus,
    TestMethod,
    VerificationEvidenceType,
    VerificationMethod,
)
from app.schemas import (
    ArtifactLinkCreate,
    BaselineCreate,
    BlockContainmentCreate,
    FMIContractCreate,
    ConfigurationContextCreate,
    ConfigurationItemMappingCreate,
    ConfigurationContextUpdate,
    ConnectorDefinitionCreate,
    ExternalArtifactCreate,
    ExternalArtifactVersionCreate,
    ProjectImportCreate,
    ProjectCreate,
    RequirementCreate,
    OperationalEvidenceCreate,
    SimulationEvidenceCreate,
    ComponentCreate,
    SysMLRelationCreate,
    TestCaseCreate,
    VerificationEvidenceCreate,
)
from app.services import (
    create_artifact_link,
    create_configuration_context,
    create_configuration_item_mapping,
    create_connector,
    create_baseline,
    create_block_containment,
    create_component,
    create_external_artifact,
    create_external_artifact_version,
    create_project,
    create_requirement,
    create_sysml_relation,
    create_test_case,
    create_operational_evidence,
    create_simulation_evidence,
    create_verification_evidence,
    create_fmi_contract,
    compare_configuration_contexts,
    export_project_bundle,
    get_authoritative_registry_summary,
    get_fmi_contract_service,
    get_configuration_context_service,
    list_external_artifacts,
    list_fmi_contracts,
    list_operational_evidence,
    seed_demo,
    update_configuration_context,
)
from app.main import (
    compare_configuration_contexts_endpoint,
    baseline_compare_endpoint,
    baseline_compare_baseline_endpoint,
    baseline_bridge_context_endpoint,
    baseline_detail_endpoint,
    create_configuration_item_mapping_endpoint,
    delete_configuration_item_mapping_endpoint,
    requirement_detail_endpoint,
    list_simulation_evidence_endpoint,
    list_operational_evidence_endpoint,
    test_case_detail_endpoint as case_detail_route,
    verification_evidence_detail_endpoint,
    import_project_records_endpoint,
    create_fmi_contract_endpoint,
    fmi_contract_detail_endpoint,
    simulation_evidence_detail_endpoint,
    operational_evidence_detail_endpoint,
    list_fmi_contracts_endpoint,
    update_configuration_context_endpoint,
    mapping_contract_endpoint,
    step_ap242_contract_endpoint,
    project_tab_stats_endpoint,
    seed_manufacturing_demo_endpoint,
    seed_personal_demo_endpoint,
)


def make_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_external_artifact_registry_versioning_and_filters():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-1", name="P-FED-1", description=""))
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(
                project_id=project.id,
                name="DOORS NG",
                connector_type=ConnectorType.doors,
                base_url="https://doors.example.local",
                description="Requirements",
            ),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="REQ-1",
                artifact_type=ExternalArtifactType.requirement,
                name="Endurance requirement",
                status=ExternalArtifactStatus.active,
            ),
        )
        version = create_external_artifact_version(
            session,
            artifact.id,
            ExternalArtifactVersionCreate(
                version_label="7",
                revision_label="7",
                checksum_or_signature="abc123",
                effective_date=date(2026, 4, 1),
                source_timestamp=datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc),
            ),
        )

        filtered = list_external_artifacts(session, project.id, connector_type=ConnectorType.doors, artifact_type=ExternalArtifactType.requirement)
        summary = get_authoritative_registry_summary(session, project.id)

        assert version.external_artifact_id == artifact.id
        assert filtered and filtered[0].connector_name == "DOORS NG"
        assert summary.connectors == 1
        assert summary.external_artifacts == 1
        assert summary.external_artifact_versions == 1
        assert summary.revision_snapshots == 0
        assert summary.revision_snapshot_integrity_status == "warning"


def test_artifact_link_requires_project_scope():
    with make_session() as session:
        project_a = create_project(session, ProjectCreate(code="P-FED-2", name="P-FED-2", description=""))
        project_b = create_project(session, ProjectCreate(code="P-FED-3", name="P-FED-3", description=""))
        requirement = Requirement(
            project_id=project_a.id,
            key="REQ-A",
            title="Requirement A",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.commit()
        session.refresh(requirement)

        connector = create_connector(
            session,
            ConnectorDefinitionCreate(
                project_id=project_b.id,
                name="Cameo",
                connector_type=ConnectorType.sysml,
            ),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project_b.id,
                connector_definition_id=connector.id,
                external_id="SYSML-1",
                artifact_type=ExternalArtifactType.sysml_element,
                name="Block",
            ),
        )

        with pytest.raises(ValueError):
            create_artifact_link(
                session,
                ArtifactLinkCreate(
                    project_id=project_a.id,
                    internal_object_type=FederatedInternalObjectType.requirement,
                    internal_object_id=requirement.id,
                    external_artifact_id=artifact.id,
                    relation_type=ArtifactLinkRelationType.maps_to,
                ),
            )


def test_configuration_context_and_mappings():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-4", name="P-FED-4", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-CTX",
            title="Context requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=3,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        block = Block(
            project_id=project.id,
            key="BLK-CTX",
            name="Context block",
            description="",
            block_kind=BlockKind.component,
            abstraction_level=AbstractionLevel.physical,
            status=BlockStatus.approved,
            version=2,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-CTX",
            title="Context test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(project_id=project.id, name="Simulink", connector_type=ConnectorType.simulation),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="SIM-1",
                artifact_type=ExternalArtifactType.simulation_model,
                name="Endurance model",
            ),
        )
        version = create_external_artifact_version(session, artifact.id, ExternalArtifactVersionCreate(version_label="1.4"))
        session.add(requirement)
        session.add(block)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(block)
        session.refresh(test_case)

        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-1",
                name="PDR 0.3",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )

        internal = create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=3,
                role_label="Approved requirement",
            ),
        )
        external = create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version.id,
                role_label="Authoritative external reference",
            ),
        )

        update_configuration_context(session, context.id, ConfigurationContextUpdate(status=ConfigurationContextStatus.frozen))

        assert internal.configuration_context_id == context.id
        assert external.external_artifact_version_id == version.id

        with pytest.raises(ValueError):
            create_configuration_item_mapping(
                session,
                context.id,
                ConfigurationItemMappingCreate(item_kind=ConfigurationItemKind.external_artifact_version),
            )


def test_sysml_mapping_contract_endpoint_exposes_explicit_mapping_shape():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-4-SYSML", name="P-FED-4-SYSML", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-SYSML",
            title="SysML requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        block = Block(
            project_id=project.id,
            key="BLK-SYSML",
            name="SysML block",
            description="",
            block_kind=BlockKind.system,
            abstraction_level=AbstractionLevel.logical,
            status=BlockStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        physical_block = Block(
            project_id=project.id,
            key="BLK-SYSML-PHY",
            name="Physical SysML block",
            description="",
            block_kind=BlockKind.assembly,
            abstraction_level=AbstractionLevel.physical,
            status=BlockStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-SYSML",
            title="SysML test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(block)
        session.add(physical_block)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(block)
        session.refresh(physical_block)
        session.refresh(test_case)

        create_sysml_relation(
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
        create_block_containment(
            session,
            BlockContainmentCreate(
                project_id=project.id,
                parent_block_id=block.id,
                child_block_id=physical_block.id,
                relation_type=BlockContainmentRelationType.contains,
            ),
        )

        contract = mapping_contract_endpoint(project.id, session)

        assert contract.contract_schema == "threadlite.sysml.mapping-contract.v1"
        assert contract.summary.requirement_count == 1
        assert contract.summary.block_count == 2
        assert contract.summary.logical_block_count == 1
        assert contract.summary.physical_block_count == 1
        assert contract.summary.satisfy_relation_count == 1
        assert contract.summary.verify_relation_count == 1
        assert contract.summary.contain_relation_count == 1
        assert contract.requirements[0].requirement.id == requirement.id
        assert contract.requirements[0].satisfy_blocks[0].object_id == block.id
        assert contract.requirements[0].verify_tests[0].object_id == test_case.id
        assert contract.blocks[0].profile_label in {"Logical block", "Physical block"}


def test_step_ap242_contract_endpoint_exports_part_metadata_and_artifacts():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-4-AP242", name="P-FED-4-AP242", description=""))
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

        contract = step_ap242_contract_endpoint(project.id, session)

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


def test_baseline_detail_endpoint_exposes_related_configuration_contexts():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-11", name="P-FED-11", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-BRIDGE",
            title="Bridge requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        block = Block(
            project_id=project.id,
            key="BLK-BRIDGE",
            name="Bridge block",
            description="",
            block_kind=BlockKind.system,
            abstraction_level=AbstractionLevel.logical,
            status=BlockStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-BRIDGE",
            title="Bridge test",
            description="",
            method=TestMethod.bench,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(block)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(block)
        session.refresh(test_case)

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

        detail = baseline_detail_endpoint(baseline.id, session)
        bridge = baseline_bridge_context_endpoint(baseline.id, session)

        assert detail["baseline"].id == baseline.id
        assert detail["bridge_context"].baseline_id == baseline.id
        assert detail["related_configuration_contexts"]
        assert detail["related_configuration_contexts"][0].id == context.id
        assert bridge.baseline_id == baseline.id
        assert bridge.item_count == 3


def test_baseline_compare_endpoint_rejects_cross_project_inputs():
    with make_session() as session:
        project_a = create_project(session, ProjectCreate(code="P-FED-12", name="P-FED-12", description=""))
        project_b = create_project(session, ProjectCreate(code="P-FED-13", name="P-FED-13", description=""))
        baseline, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project_a.id,
                name="Cross project baseline",
                description="Baseline for compare",
            ),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_b.id,
                key="CTX-X",
                name="Foreign context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )

        with pytest.raises(HTTPException, match="same project"):
            baseline_compare_endpoint(baseline.id, context.id, session)


def test_baseline_compare_baseline_endpoint_rejects_cross_project_inputs():
    with make_session() as session:
        project_a = create_project(session, ProjectCreate(code="P-FED-14", name="P-FED-14", description=""))
        project_b = create_project(session, ProjectCreate(code="P-FED-15", name="P-FED-15", description=""))
        left, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project_a.id,
                name="Left baseline",
                description="Baseline for compare",
            ),
        )
        right, _ = create_baseline(
            session,
            BaselineCreate(
                project_id=project_b.id,
                name="Right baseline",
                description="Baseline for compare",
            ),
        )

        with pytest.raises(HTTPException, match="same project"):
            baseline_compare_baseline_endpoint(left.id, right.id, session)


def test_configuration_context_resolved_view_exposes_external_revision_metadata():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-10", name="P-FED-10", description=""))
        connector = create_connector(
            session,
            ConnectorDefinitionCreate(project_id=project.id, name="Simulink", connector_type=ConnectorType.simulation),
        )
        artifact = create_external_artifact(
            session,
            ExternalArtifactCreate(
                project_id=project.id,
                connector_definition_id=connector.id,
                external_id="SIM-REV",
                artifact_type=ExternalArtifactType.simulation_model,
                name="Revision model",
            ),
        )
        version = create_external_artifact_version(
            session,
            artifact.id,
            ExternalArtifactVersionCreate(version_label="3.2", revision_label="R7"),
        )
        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-REV",
                name="Revision context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        create_configuration_item_mapping(
            session,
            context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version.id,
                role_label="Authoritative reference",
            ),
        )
        update_configuration_context(session, context.id, ConfigurationContextUpdate(status=ConfigurationContextStatus.frozen))

        detail = get_configuration_context_service(session, context.id)
        external = detail["resolved_view"]["external"][0]

        assert external["connector_name"] == "Simulink"
        assert external["artifact_name"] == "Revision model"
        assert external["version_label"] == "3.2"
        assert external["revision_label"] == "R7"
        assert external["external_artifact_id"] == str(artifact.id)
        assert external["external_artifact_version_id"] == str(version.id)


def test_configuration_context_compare_groups_added_removed_and_version_changes():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-5", name="P-FED-5", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-COMP",
            title="Compare requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=2,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        block = Block(
            project_id=project.id,
            key="BLK-COMP",
            name="Compare block",
            description="",
            block_kind=BlockKind.system,
            abstraction_level=AbstractionLevel.logical,
            status=BlockStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-COMP",
            title="Compare test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
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
                external_id="SYSML-COMP",
                artifact_type=ExternalArtifactType.sysml_element,
                name="Compare artifact",
            ),
        )
        version_1 = create_external_artifact_version(session, artifact.id, ExternalArtifactVersionCreate(version_label="1.0"))
        version_2 = create_external_artifact_version(session, artifact.id, ExternalArtifactVersionCreate(version_label="2.0"))
        session.add(requirement)
        session.add(block)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(block)
        session.refresh(test_case)
        left = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-LEFT",
                name="Left context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        right = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-RIGHT",
                name="Right context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )

        create_configuration_item_mapping(
            session,
            left.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=2,
                role_label="Common requirement",
            ),
        )
        create_configuration_item_mapping(
            session,
            left.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_test_case,
                internal_object_type=FederatedInternalObjectType.test_case,
                internal_object_id=test_case.id,
                internal_object_version=1,
                role_label="Left only",
            ),
        )
        create_configuration_item_mapping(
            session,
            left.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version_1.id,
                role_label="Baseline export",
            ),
        )
        create_configuration_item_mapping(
            session,
            right.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_block,
                internal_object_type=FederatedInternalObjectType.block,
                internal_object_id=block.id,
                internal_object_version=1,
                role_label="Right only",
            ),
        )
        create_configuration_item_mapping(
            session,
            right.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.external_artifact_version,
                external_artifact_version_id=version_2.id,
                role_label="Baseline export",
            ),
        )
        session.add(
            ConfigurationItemMapping(
                configuration_context_id=right.id,
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=3,
                role_label="Common requirement",
            )
        )
        session.commit()

        comparison = compare_configuration_contexts(session, left.id, right.id)

        assert comparison.summary.added == 1
        assert comparison.summary.removed == 1
        assert comparison.summary.version_changed == 2
        assert comparison.groups
        assert any(group.item_kind == ConfigurationItemKind.internal_block and group.added for group in comparison.groups)
        assert any(group.item_kind == ConfigurationItemKind.internal_test_case and group.removed for group in comparison.groups)
        assert any(
            group.item_kind == ConfigurationItemKind.internal_requirement and group.version_changed for group in comparison.groups
        )
        assert any(group.item_kind == ConfigurationItemKind.external_artifact_version and group.version_changed for group in comparison.groups)


def test_compare_configuration_contexts_endpoint_rejects_cross_project_inputs():
    with make_session() as session:
        project_a = create_project(session, ProjectCreate(code="P-FED-8", name="P-FED-8", description=""))
        project_b = create_project(session, ProjectCreate(code="P-FED-9", name="P-FED-9", description=""))
        left = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_a.id,
                key="CTX-A",
                name="Left context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )
        right = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project_b.id,
                key="CTX-B",
                name="Right context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
            ),
        )

        with pytest.raises(HTTPException) as excinfo:
            compare_configuration_contexts_endpoint(left.id, right.id, session)

        assert excinfo.value.status_code == 400
        assert "same project" in str(excinfo.value.detail)


def test_immutable_configuration_context_routes_reject_mutation():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-10", name="P-FED-10", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-LOCK",
            title="Locked requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.commit()
        session.refresh(requirement)

        context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-LOCK",
                name="Locked context",
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
                internal_object_version=1,
            ),
        )
        create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-REL",
                name="Released context",
                context_type=ConfigurationContextType.released,
                status=ConfigurationContextStatus.active,
            ),
        )
        update_configuration_context(session, context.id, ConfigurationContextUpdate(status=ConfigurationContextStatus.frozen))

        obsolete_context = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-OBS",
                name="Obsolete context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.active,
            ),
        )
        obsolete_mapping = create_configuration_item_mapping(
            session,
            obsolete_context.id,
            ConfigurationItemMappingCreate(
                item_kind=ConfigurationItemKind.internal_requirement,
                internal_object_type=FederatedInternalObjectType.requirement,
                internal_object_id=requirement.id,
                internal_object_version=requirement.version,
            ),
        )
        update_configuration_context(session, obsolete_context.id, ConfigurationContextUpdate(status=ConfigurationContextStatus.obsolete))

        with pytest.raises(HTTPException) as update_exc:
            update_configuration_context_endpoint(context.id, ConfigurationContextUpdate(name="Still locked"), session)
        assert update_exc.value.status_code == 400

        with pytest.raises(HTTPException) as create_exc:
            create_configuration_item_mapping_endpoint(
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
                session,
            )
        assert create_exc.value.status_code == 400

        with pytest.raises(HTTPException) as delete_exc:
            delete_configuration_item_mapping_endpoint(mapping.id, session)
        assert delete_exc.value.status_code == 400

        with pytest.raises(HTTPException) as obsolete_update_exc:
            update_configuration_context_endpoint(obsolete_context.id, ConfigurationContextUpdate(name="Still obsolete"), session)
        assert obsolete_update_exc.value.status_code == 400

        with pytest.raises(HTTPException) as obsolete_create_exc:
            create_configuration_item_mapping_endpoint(
                obsolete_context.id,
                ConfigurationItemMappingCreate(
                    item_kind=ConfigurationItemKind.external_artifact_version,
                    external_artifact_version_id=create_external_artifact_version(
                        session,
                        create_external_artifact(
                            session,
                            ExternalArtifactCreate(
                                project_id=project.id,
                                external_id="ART-OBS",
                                artifact_type=ExternalArtifactType.document,
                                name="Obsolete artifact",
                            ),
                        ).id,
                        ExternalArtifactVersionCreate(version_label="1"),
                    ).id,
                ),
                session,
            )
        assert obsolete_create_exc.value.status_code == 400

        with pytest.raises(HTTPException) as obsolete_delete_exc:
            delete_configuration_item_mapping_endpoint(obsolete_mapping.id, session)
        assert obsolete_delete_exc.value.status_code == 400


def test_baseline_detail_endpoint_exposes_related_configuration_contexts():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-11", name="P-FED-11", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-BRIDGE",
            title="Bridge requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        block = Block(
            project_id=project.id,
            key="BLK-BRIDGE",
            name="Bridge block",
            description="",
            block_kind=BlockKind.system,
            abstraction_level=AbstractionLevel.logical,
            status=BlockStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-BRIDGE",
            title="Bridge test",
            description="",
            method=TestMethod.bench,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(block)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(block)
        session.refresh(test_case)

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

        detail = baseline_detail_endpoint(baseline.id, session)
        assert detail["related_configuration_contexts"]
        assert detail["related_configuration_contexts"][0].id == context.id


def test_requirement_and_test_case_detail_endpoints_expose_verification_evidence():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-12", name="P-FED-12", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-EVID",
            title="Evidence requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.test,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-EVID",
            title="Evidence test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(test_case)

        evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Flight validation report",
                evidence_type=VerificationEvidenceType.test_result,
                summary="The flight test passed endurance criteria.",
                source_name="LabRig",
                source_reference="report-42",
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        requirement_detail = requirement_detail_endpoint(requirement.id, session)
        test_case_detail = case_detail_route(test_case.id, session)
        evidence_detail = verification_evidence_detail_endpoint(evidence.id, session)

        assert requirement_detail["verification_evidence"]
        assert test_case_detail["verification_evidence"]
        assert requirement_detail["verification_evidence"][0].id == evidence.id
        assert test_case_detail["verification_evidence"][0].id == evidence.id
        assert evidence_detail.id == evidence.id


def test_simulation_evidence_endpoints_expose_first_class_records_and_filters():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-12B", name="P-FED-12B", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-SIM",
            title="Simulation requirement",
            description="",
            category=RequirementCategory.performance,
            priority=Priority.high,
            verification_method=VerificationMethod.analysis,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-SIM",
            title="Simulation test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(test_case)

        verification_evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Verification evidence bridge",
                evidence_type=VerificationEvidenceType.simulation,
                summary="Legacy record linked to simulation evidence.",
                source_name="Simulink",
                source_reference="SIM-LEGACY-2",
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
                scenario_name="Nominal envelope",
                input_summary="Standard conditions",
                inputs_json={"ambient_c": 25},
                expected_behavior="Remain within envelope.",
                observed_behavior="Remain within envelope.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL"},
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
                linked_verification_evidence_ids=[verification_evidence.id],
            ),
        )

        listed = list_simulation_evidence_endpoint(project.id, session=session)
        by_requirement = list_simulation_evidence_endpoint(
            project.id,
            internal_object_type=SimulationEvidenceLinkObjectType.requirement,
            internal_object_id=requirement.id,
            session=session,
        )
        detail = simulation_evidence_detail_endpoint(evidence.id, session)

        assert listed
        assert listed[0].id == evidence.id
        assert by_requirement
        assert by_requirement[0].id == evidence.id
        assert detail.id == evidence.id
        assert any(obj.object_type == "verification_evidence" for obj in detail.linked_objects)


def test_fmi_contract_endpoints_expose_model_reference_structure_and_exports():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-FMI", name="FMI federation", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-FMI",
            title="FMI requirement",
            description="",
            category=RequirementCategory.environment,
            priority=Priority.medium,
            verification_method=VerificationMethod.analysis,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        test_case = TestCase(
            project_id=project.id,
            key="TST-FMI",
            title="FMI test",
            description="",
            method=TestMethod.simulation,
            status=TestCaseStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.add(test_case)
        session.commit()
        session.refresh(requirement)
        session.refresh(test_case)

        contract = create_fmi_contract_endpoint(
            project.id,
            FMIContractCreate(
                project_id=project.id,
                key="FMI-FED-001",
                name="Federation FMI contract",
                description="Route test placeholder",
                model_identifier="SIM-FLIGHT-ENDURANCE",
                model_version="1.4",
                model_uri="federation://SIM-FLIGHT-ENDURANCE",
                adapter_profile="simulink-placeholder",
                metadata_json={"adapter_capability": "simulation_metadata"},
            ),
            session=session,
        )
        evidence = create_simulation_evidence(
            session,
            SimulationEvidenceCreate(
                project_id=project.id,
                title="Thermal simulation result",
                model_reference="Thermal Model",
                scenario_name="Nominal envelope",
                input_summary="Standard conditions",
                inputs_json={"ambient_c": 25},
                expected_behavior="Remain within envelope.",
                observed_behavior="Remain within envelope.",
                result=SimulationEvidenceResult.passed,
                execution_timestamp=datetime.now(timezone.utc),
                fmi_contract_id=contract.id,
                metadata_json={"contract_reference": "FMI-placeholder:THERMAL"},
                linked_requirement_ids=[requirement.id],
                linked_test_case_ids=[test_case.id],
            ),
        )

        listed = list_fmi_contracts_endpoint(project.id, session=session)
        detail = fmi_contract_detail_endpoint(contract.id, session)
        evidence_detail = simulation_evidence_detail_endpoint(evidence.id, session)
        bundle = export_project_bundle(session, project.id)

        assert listed
        assert listed[0].id == contract.id
        assert detail.fmi_contract.id == contract.id
        assert detail.simulation_evidence[0].id == evidence.id
        assert evidence_detail.fmi_contract_id == contract.id
        assert bundle["fmi_contracts"][0]["id"] == str(contract.id)
        assert bundle["simulation_evidence"][0]["fmi_contract_id"] == str(contract.id)


def test_operational_evidence_endpoints_expose_first_class_records_and_filters():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-FED-12C", name="P-FED-12C", description=""))
        requirement = Requirement(
            project_id=project.id,
            key="REQ-OP",
            title="Operational requirement",
            description="",
            category=RequirementCategory.operations,
            priority=Priority.high,
            verification_method=VerificationMethod.demonstration,
            status=RequirementStatus.approved,
            version=1,
            approved_at=datetime.now(timezone.utc),
            approved_by="seed",
        )
        session.add(requirement)
        session.commit()
        session.refresh(requirement)

        verification_evidence = create_verification_evidence(
            session,
            VerificationEvidenceCreate(
                project_id=project.id,
                title="Operational verification evidence",
                evidence_type=VerificationEvidenceType.telemetry,
                summary="Telemetry record for operational batch linkage.",
                observed_at=datetime.now(timezone.utc),
                source_name="Telemetry hub",
                source_reference="OP-VER-2",
                linked_requirement_ids=[requirement.id],
            ),
        )
        evidence = create_operational_evidence(
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
                metadata_json={"contract_reference": "OP-EVBATCH:2"},
                linked_requirement_ids=[requirement.id],
                linked_verification_evidence_ids=[verification_evidence.id],
            ),
        )

        listed = list_operational_evidence_endpoint(project.id, session=session)
        by_requirement = list_operational_evidence_endpoint(
            project.id,
            internal_object_type=OperationalEvidenceLinkObjectType.requirement,
            internal_object_id=requirement.id,
            session=session,
        )
        by_verification = list_operational_evidence_endpoint(
            project.id,
            internal_object_type=OperationalEvidenceLinkObjectType.verification_evidence,
            internal_object_id=verification_evidence.id,
            session=session,
        )
        detail = operational_evidence_detail_endpoint(evidence.id, session)

        assert listed
        assert listed[0].id == evidence.id
        assert by_requirement
        assert by_requirement[0].id == evidence.id
        assert by_verification
        assert by_verification[0].id == evidence.id
        assert detail.id == evidence.id
        assert {obj.object_type for obj in detail.linked_objects} == {"requirement", "verification_evidence"}


def test_export_bundle_includes_federation_objects():
    with make_session() as session:
        seed_demo(session)
        project = session.exec(select(Project).where(Project.code == "DRONE-001")).one()
        bundle = export_project_bundle(session, project.id)

        assert bundle["connectors"]
        assert bundle["external_artifacts"]
        assert bundle["external_artifact_versions"]
        assert bundle["artifact_links"]
        assert bundle["configuration_contexts"]
        assert bundle["configuration_item_mappings"]
        assert bundle["authoritative_registry_summary"]["connectors"] >= 4


def test_profile_seed_endpoints_create_profile_specific_projects():
    with make_session() as session:
        manufacturing = seed_manufacturing_demo_endpoint(session=session)
        personal = seed_personal_demo_endpoint(session=session)

        manufacturing_project = session.exec(select(Project).where(Project.code == "MFG-001")).one()
        personal_project = session.exec(select(Project).where(Project.code == "HOME-001")).one()

        assert manufacturing["seeded"] is True
        assert personal["seeded"] is True
        assert manufacturing_project.domain_profile == "manufacturing"
        assert personal_project.domain_profile == "personal"


def test_project_tab_stats_endpoint_reports_core_thread_counts():
    with make_session() as session:
        seed_manufacturing_demo_endpoint(session=session)
        project = session.exec(select(Project).where(Project.code == "MFG-001")).one()

        stats = project_tab_stats_endpoint(project.id, session=session)

        assert stats.requirements >= 8
        assert stats.blocks >= 6
        assert stats.tests >= 8
        assert stats.baselines >= 1
        assert stats.change_requests >= 1
        assert stats.simulation_evidence >= 2
        assert stats.operational_evidence >= 2


def test_csv_import_endpoint_creates_external_artifacts_and_verification_evidence():
    with make_session() as session:
        project = create_project(session, ProjectCreate(code="P-IMP-CSV", name="P-IMP-CSV", description=""))
        requirement = create_requirement(
            session,
            RequirementCreate(
                project_id=project.id,
                key="REQ-IMP-CSV",
                title="CSV imported requirement",
                category=RequirementCategory.performance,
                priority=Priority.high,
                verification_method=VerificationMethod.test,
            ),
        )
        test_case = create_test_case(
            session,
            TestCaseCreate(
                project_id=project.id,
                key="TST-IMP-CSV",
                title="CSV imported test case",
                method=TestMethod.bench,
                status=TestCaseStatus.approved,
            ),
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "record_type",
            "external_id",
            "artifact_type",
            "name",
            "description",
            "status",
            "title",
            "evidence_type",
            "summary",
            "observed_at",
            "source_name",
            "source_reference",
            "linked_requirement_ids",
            "linked_test_case_ids",
            "metadata_json",
        ])
        writer.writerow([
            "external_artifact",
            "EXT-IMP-CSV-1",
            "document",
            "CSV imported document",
            "Imported via CSV",
            "active",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "{}",
        ])
        writer.writerow([
            "verification_evidence",
            "",
            "",
            "",
            "",
            "",
            "CSV imported evidence",
            "analysis",
            "CSV import evidence",
            datetime.now(timezone.utc).isoformat(),
            "CSV tool",
            "IMP-CSV-1",
            str(requirement.id),
            str(test_case.id),
            "{}",
        ])

        payload = ProjectImportCreate(format="csv", content=buffer.getvalue())
        result = import_project_records_endpoint(project.id, payload, session=session)

        assert result.summary.parsed_records == 2
        assert result.summary.created_external_artifacts == 1
        assert result.summary.created_verification_evidence == 1
        assert result.external_artifacts[0].external_id == "EXT-IMP-CSV-1"
        assert {item.object_id for item in result.verification_evidence[0].linked_objects} == {requirement.id, test_case.id}

