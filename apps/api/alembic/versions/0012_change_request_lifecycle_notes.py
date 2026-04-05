"""change request lifecycle notes

Revision ID: 0012_change_request_lifecycle_notes
Revises: 0011_requirement_criteria_and_ast_guard
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_change_request_lifecycle_notes"
down_revision = "0011_requirement_criteria_and_ast_guard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("change_requests") as batch_op:
        batch_op.add_column(sa.Column("analysis_summary", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("disposition_summary", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("implementation_summary", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("closure_summary", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("change_requests") as batch_op:
        batch_op.drop_column("closure_summary")
        batch_op.drop_column("implementation_summary")
        batch_op.drop_column("disposition_summary")
        batch_op.drop_column("analysis_summary")

