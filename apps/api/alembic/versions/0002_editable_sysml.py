"""editable sysml workflow

Revision ID: 0002_editable_sysml
Revises: 0001_initial
Create Date: 2026-04-03
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_editable_sysml"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    inspector = sa.inspect(bind)
    sysml_object_type = sa.Enum("requirement", "block", "test_case", "component", "operational_run", name="sysmlobjecttype")
    sysml_relation_type = sa.Enum("satisfy", "verify", "deriveReqt", "refine", "trace", "allocate", "contain", name="sysmlrelationtype")
    block_containment_relation_type = sa.Enum("contains", "composed_of", name="blockcontainmentrelationtype")

    if inspector.has_table("blocks"):
        return

    if dialect == "postgresql":
        for enum_name, values in {
            "requirementstatus": ["in_review", "rejected", "obsolete"],
            "testcasestatus": ["in_review", "approved", "rejected", "obsolete"],
            "baselineobjecttype": ["block"],
        }.items():
            for value in values:
                op.execute(sa.text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))

    op.add_column("requirements", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("requirements", sa.Column("approved_by", sa.String(length=255), nullable=True))
    op.add_column("requirements", sa.Column("rejection_reason", sa.String(), nullable=True))
    op.add_column("requirements", sa.Column("review_comment", sa.String(), nullable=True))

    op.add_column("test_cases", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("test_cases", sa.Column("approved_by", sa.String(length=255), nullable=True))
    op.add_column("test_cases", sa.Column("rejection_reason", sa.String(), nullable=True))
    op.add_column("test_cases", sa.Column("review_comment", sa.String(), nullable=True))

    op.create_table(
        "blocks",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("block_kind", sa.Enum("system", "subsystem", "assembly", "component", "software", "interface", "other", name="blockkind"), nullable=False),
        sa.Column("abstraction_level", sa.Enum("logical", "physical", name="abstractionlevel"), nullable=False),
        sa.Column("status", sa.Enum("draft", "in_review", "approved", "rejected", "obsolete", name="blockstatus"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("rejection_reason", sa.String(), nullable=True),
        sa.Column("review_comment", sa.String(), nullable=True),
    )
    op.create_table(
        "block_containments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("parent_block_id", sa.Uuid(), sa.ForeignKey("blocks.id"), nullable=False),
        sa.Column("child_block_id", sa.Uuid(), sa.ForeignKey("blocks.id"), nullable=False),
        sa.Column("relation_type", block_containment_relation_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "sysml_relations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("source_type", sysml_object_type, nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sysml_object_type, nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("relation_type", sysml_relation_type, nullable=False),
        sa.Column("rationale", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "revision_snapshots",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_by", sa.String(length=255), nullable=True),
        sa.Column("change_summary", sa.String(), nullable=True),
    )
    op.create_table(
        "approval_action_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=False),
        sa.Column("object_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=False),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("approval_action_logs")
    op.drop_table("revision_snapshots")
    op.drop_table("sysml_relations")
    op.drop_table("block_containments")
    op.drop_table("blocks")
    op.drop_column("test_cases", "review_comment")
    op.drop_column("test_cases", "rejection_reason")
    op.drop_column("test_cases", "approved_by")
    op.drop_column("test_cases", "approved_at")
    op.drop_column("requirements", "review_comment")
    op.drop_column("requirements", "rejection_reason")
    op.drop_column("requirements", "approved_by")
    op.drop_column("requirements", "approved_at")
