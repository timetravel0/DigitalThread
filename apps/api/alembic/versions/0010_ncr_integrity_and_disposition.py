"""ncr integrity and disposition

Revision ID: 0010_ncr_integrity_and_disposition
Revises: 0009_fmi_placeholder_contract
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_ncr_integrity_and_disposition"
down_revision = "0009_fmi_placeholder_contract"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("non_conformities") as batch_op:
        batch_op.add_column(sa.Column("disposition", sa.Enum("accept", "rework", "reject", name="nonconformitydisposition"), nullable=True))
        batch_op.add_column(sa.Column("review_comment", sa.String(), nullable=True))
    with op.batch_alter_table("revision_snapshots") as batch_op:
        batch_op.add_column(sa.Column("snapshot_hash", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("previous_snapshot_hash", sa.String(length=128), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("revision_snapshots") as batch_op:
        batch_op.drop_column("previous_snapshot_hash")
        batch_op.drop_column("snapshot_hash")
    with op.batch_alter_table("non_conformities") as batch_op:
        batch_op.drop_column("review_comment")
        batch_op.drop_column("disposition")

