"""operational evidence batches

Revision ID: 0008_operational_evidence
Revises: 0007_simulation_evidence
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_operational_evidence"
down_revision = "0007_simulation_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("operational_evidence_batches"):
        op.create_table(
            "operational_evidence_batches",
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("source_name", sa.String(length=255), nullable=False),
            sa.Column("source_type", sa.Enum("sensor", "system", name="operationalevidencesourcetype"), nullable=False),
            sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("coverage_window_start", sa.DateTime(timezone=True), nullable=False),
            sa.Column("coverage_window_end", sa.DateTime(timezone=True), nullable=False),
            sa.Column("observations_summary", sa.String(), nullable=False, server_default=""),
            sa.Column("aggregated_observations_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("quality_status", sa.Enum("good", "warning", "poor", "unknown", name="operationalevidencequalitystatus"), nullable=False),
            sa.Column("derived_metrics_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        )

    if not inspector.has_table("operational_evidence_links"):
        op.create_table(
            "operational_evidence_links",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("operational_evidence_id", sa.Uuid(), sa.ForeignKey("operational_evidence_batches.id"), nullable=False),
            sa.Column(
                "internal_object_type",
                sa.Enum("requirement", "verification_evidence", name="operationalevidencelinkobjecttype"),
                nullable=False,
            ),
            sa.Column("internal_object_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("operational_evidence_links"):
        op.drop_table("operational_evidence_links")
    if inspector.has_table("operational_evidence_batches"):
        op.drop_table("operational_evidence_batches")
