"""verification evidence model

Revision ID: 0004_verification_evidence
Revises: 0003_authoritative_sources
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_verification_evidence"
down_revision = "0003_authoritative_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verification_evidence",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("evidence_type", sa.Enum("test_result", "simulation", "telemetry", "analysis", "inspection", "other", name="verificationevidencetype"), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_name", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "verification_evidence_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("verification_evidence_id", sa.Uuid(), sa.ForeignKey("verification_evidence.id"), nullable=False),
        sa.Column("internal_object_type", sa.Enum("project", "requirement", "block", "test_case", "baseline", "change_request", "component", name="federatedinternalobjecttype"), nullable=False),
        sa.Column("internal_object_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("verification_evidence_links")
    op.drop_table("verification_evidence")
