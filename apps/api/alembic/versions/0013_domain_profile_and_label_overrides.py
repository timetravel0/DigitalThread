"""domain profile and label overrides

Revision ID: 0013_domain_profile_and_label_overrides
Revises: 0012_change_request_lifecycle_notes
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_domain_profile_and_label_overrides"
down_revision = "0012_change_request_lifecycle_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("domain_profile", sa.String(length=32), nullable=False, server_default="engineering"))
        batch_op.add_column(sa.Column("label_overrides", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("label_overrides")
        batch_op.drop_column("domain_profile")

