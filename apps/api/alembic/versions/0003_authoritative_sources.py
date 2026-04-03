"""authoritative sources and federation

Revision ID: 0003_authoritative_sources
Revises: 0002_editable_sysml
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_authoritative_sources"
down_revision = "0002_editable_sysml"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "connector_definitions",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("connector_type", sa.Enum("doors", "sysml", "plm", "simulation", "test", "telemetry", "custom", name="connectortype"), nullable=False),
        sa.Column("base_url", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_table(
        "external_artifacts",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("connector_definition_id", sa.Uuid(), sa.ForeignKey("connector_definitions.id"), nullable=True),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("artifact_type", sa.Enum("requirement", "sysml_element", "block", "cad_part", "software_module", "test_case", "simulation_model", "test_result", "telemetry_source", "document", "other", name="externalartifacttype"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("canonical_uri", sa.String(), nullable=True),
        sa.Column("native_tool_url", sa.String(), nullable=True),
        sa.Column("status", sa.Enum("active", "deprecated", "obsolete", name="externalartifactstatus"), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_table(
        "external_artifact_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("external_artifact_id", sa.Uuid(), sa.ForeignKey("external_artifacts.id"), nullable=False),
        sa.Column("version_label", sa.String(length=64), nullable=False),
        sa.Column("revision_label", sa.String(length=64), nullable=True),
        sa.Column("checksum_or_signature", sa.String(length=255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "artifact_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("internal_object_type", sa.Enum("project", "requirement", "block", "test_case", "baseline", "change_request", "component", name="federatedinternalobjecttype"), nullable=False),
        sa.Column("internal_object_id", sa.Uuid(), nullable=False),
        sa.Column("external_artifact_id", sa.Uuid(), sa.ForeignKey("external_artifacts.id"), nullable=False),
        sa.Column("external_artifact_version_id", sa.Uuid(), sa.ForeignKey("external_artifact_versions.id"), nullable=True),
        sa.Column("relation_type", sa.Enum("authoritative_reference", "derived_from_external", "synchronized_with", "validated_against", "exported_to", "maps_to", name="artifactlinkrelationtype"), nullable=False),
        sa.Column("rationale", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "configuration_contexts",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("context_type", sa.Enum("working", "baseline_candidate", "review_gate", "released", "imported", name="configurationcontexttype"), nullable=False),
        sa.Column("status", sa.Enum("draft", "active", "frozen", "obsolete", name="configurationcontextstatus"), nullable=False),
    )
    op.create_table(
        "configuration_item_mappings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("configuration_context_id", sa.Uuid(), sa.ForeignKey("configuration_contexts.id"), nullable=False),
        sa.Column("item_kind", sa.Enum("internal_requirement", "internal_block", "internal_test_case", "baseline_item", "external_artifact_version", name="configurationitemkind"), nullable=False),
        sa.Column("internal_object_type", sa.Enum("project", "requirement", "block", "test_case", "baseline", "change_request", "component", name="federatedinternalobjecttype"), nullable=True),
        sa.Column("internal_object_id", sa.Uuid(), nullable=True),
        sa.Column("internal_object_version", sa.Integer(), nullable=True),
        sa.Column("external_artifact_version_id", sa.Uuid(), sa.ForeignKey("external_artifact_versions.id"), nullable=True),
        sa.Column("role_label", sa.String(length=128), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("configuration_item_mappings")
    op.drop_table("configuration_contexts")
    op.drop_table("artifact_links")
    op.drop_table("external_artifact_versions")
    op.drop_table("external_artifacts")
    op.drop_table("connector_definitions")

