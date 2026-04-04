"""simulation evidence model

Revision ID: 0007_simulation_evidence
Revises: 0006_change_request_lifecycle
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_simulation_evidence"
down_revision = "0006_change_request_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "simulation_evidence",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("model_reference", sa.String(length=255), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("input_summary", sa.String(), nullable=True),
        sa.Column("inputs_json", sa.JSON(), nullable=False),
        sa.Column("expected_behavior", sa.String(), nullable=False),
        sa.Column("observed_behavior", sa.String(), nullable=False),
        sa.Column("result", sa.Enum("passed", "failed", "partial", name="simulationevidenceresult"), nullable=False),
        sa.Column("execution_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "simulation_evidence_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("simulation_evidence_id", sa.Uuid(), sa.ForeignKey("simulation_evidence.id"), nullable=False),
        sa.Column(
            "internal_object_type",
            sa.Enum("requirement", "test_case", "verification_evidence", name="simulationevidencelinkobjecttype"),
            nullable=False,
        ),
        sa.Column("internal_object_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("simulation_evidence_links")
    op.drop_table("simulation_evidence")
