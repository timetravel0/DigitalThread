"""requirement criteria and ast guard

Revision ID: 0011_requirement_criteria_and_ast_guard
Revises: 0010_ncr_integrity_and_disposition
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_requirement_criteria_and_ast_guard"
down_revision = "0010_ncr_integrity_and_disposition"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("requirements") as batch_op:
        batch_op.add_column(sa.Column("verification_criteria_json", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    with op.batch_alter_table("requirements") as batch_op:
        batch_op.drop_column("verification_criteria_json")

