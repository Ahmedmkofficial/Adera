"""add scam case recipient_phone

Revision ID: f1a2b3c4d5e6
Revises: e6f2a8b7c9d0
Create Date: 2026-10-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e6f2a8b7c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scam_cases",
        sa.Column("recipient_phone", sa.String(length=20), nullable=False, server_default=""),
    )
    op.alter_column("scam_cases", "recipient_phone", server_default=None)


def downgrade() -> None:
    op.drop_column("scam_cases", "recipient_phone")
