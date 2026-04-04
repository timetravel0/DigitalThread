"""fmi placeholder contract

Revision ID: 0009_fmi_placeholder_contract
Revises: 0008_operational_evidence
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_fmi_placeholder_contract"
down_revision = "0008_operational_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fmi_contracts",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("model_identifier", sa.String(length=255), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("model_uri", sa.String(), nullable=True),
        sa.Column("adapter_profile", sa.String(length=255), nullable=True),
        sa.Column("contract_version", sa.String(length=64), nullable=False, server_default="fmi.placeholder.v1"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
    )
    with op.batch_alter_table("simulation_evidence") as batch_op:
        batch_op.add_column(sa.Column("fmi_contract_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key("fk_simulation_evidence_fmi_contract_id", "fmi_contracts", ["fmi_contract_id"], ["id"])
    op.create_index("ix_simulation_evidence_fmi_contract_id", "simulation_evidence", ["fmi_contract_id"])


def downgrade() -> None:
    op.drop_index("ix_simulation_evidence_fmi_contract_id", table_name="simulation_evidence")
    with op.batch_alter_table("simulation_evidence") as batch_op:
        batch_op.drop_constraint("fk_simulation_evidence_fmi_contract_id", type_="foreignkey")
        batch_op.drop_column("fmi_contract_id")
    op.drop_table("fmi_contracts")
