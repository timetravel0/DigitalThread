from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    ArtifactLinkRelationType,
    Block,
    BlockKind,
    AbstractionLevel,
    BlockStatus,
    ConfigurationContextStatus,
    ConfigurationContextType,
    ConfigurationItemKind,
    ConfigurationItemMapping,
    ConnectorDefinition,
    ConnectorType,
    ExternalArtifact,
    ExternalArtifactStatus,
    ExternalArtifactType,
    FederatedInternalObjectType,
    Priority,
    Project,
    Requirement,
    RequirementCategory,
    RequirementStatus,
    TestCase,
    TestCaseStatus,
    TestMethod,
    VerificationEvidenceType,
    VerificationMethod,
)
from app.schemas import (
    ArtifactLinkCreate,
    BaselineCreate,
    ConfigurationContextCreate,
    ConfigurationItemMappingCreate,
    ConfigurationContextUpdate,
    ConnectorDefinitionCreate,
    ExternalArtifactCreate,
    ExternalArtifactVersionCreate,
    ProjectCreate,
    RequirementCreate,
    TestCaseCreate,
    VerificationEvidenceCreate,
)
from app.services import (
    create_artifact_link,
    create_configuration_context,
    create_configuration_item_mapping,
    create_connector,
    create_baseline,
    create_external_artifact,
    create_external_artifact_version,
    create_project,
    create_verification_evidence,
    compare_configuration_contexts,
    export_project_bundle,
    get_authoritative_registry_summary,
    get_configuration_context_service,
    list_external_artifacts,
    seed_demo,
)
from app.main import (
    compare_configuration_contexts_endpoint,
    baseline_detail_endpoint,
    create_configuration_item_mapping_endpoint,
    delete_configuration_item_mapping_endpoint,
    requirement_detail_endpoint,
    test_case_detail_endpoint,
    verification_evidence_detail_endpoint,
    update_configuration_context_endpoint,
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
                status=ConfigurationContextStatus.frozen,
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

        assert internal.configuration_context_id == context.id
        assert external.external_artifact_version_id == version.id

        with pytest.raises(ValueError):
            create_configuration_item_mapping(
                session,
                context.id,
                ConfigurationItemMappingCreate(item_kind=ConfigurationItemKind.external_artifact_version),
            )


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

        assert detail["baseline"].id == baseline.id
        assert detail["related_configuration_contexts"]
        assert detail["related_configuration_contexts"][0].id == context.id


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
                status=ConfigurationContextStatus.frozen,
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
                status=ConfigurationContextStatus.frozen,
            ),
        )
        right = create_configuration_context(
            session,
            ConfigurationContextCreate(
                project_id=project.id,
                key="CTX-RIGHT",
                name="Right context",
                context_type=ConfigurationContextType.review_gate,
                status=ConfigurationContextStatus.frozen,
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
        test_case_detail = test_case_detail_endpoint(test_case.id, session)
        evidence_detail = verification_evidence_detail_endpoint(evidence.id, session)

        assert requirement_detail["verification_evidence"]
        assert test_case_detail["verification_evidence"]
        assert requirement_detail["verification_evidence"][0].id == evidence.id
        assert test_case_detail["verification_evidence"][0].id == evidence.id
        assert evidence_detail.id == evidence.id


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
