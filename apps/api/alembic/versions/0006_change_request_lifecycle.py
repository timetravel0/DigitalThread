"""change request lifecycle expansion

Revision ID: 0006_change_request_lifecycle
Revises: 0005_non_conformity
Create Date: 2026-04-03
"""

from alembic import op


revision = "0006_change_request_lifecycle"
down_revision = "0005_non_conformity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE changerequeststatus ADD VALUE IF NOT EXISTS 'closed'")


def downgrade() -> None:
    # PostgreSQL enums cannot reliably remove values in place; this migration is one-way.
    pass
