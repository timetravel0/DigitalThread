"""non-conformity entity

Revision ID: 0005_non_conformity
Revises: 0004_verification_evidence
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_non_conformity"
down_revision = "0004_verification_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE linkobjecttype ADD VALUE IF NOT EXISTS 'non_conformity'")
        op.execute("ALTER TYPE federatedinternalobjecttype ADD VALUE IF NOT EXISTS 'non_conformity'")

    op.create_table(
        "non_conformities",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("detected", "analyzing", "contained", "corrected", "verified", "closed", name="nonconformitystatus"), nullable=False),
        sa.Column("severity", sa.Enum("low", "medium", "high", "critical", name="severity"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("non_conformities")
