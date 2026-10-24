"""batch2 schema updates

Revision ID: d5f4a1e2b3c4
Revises: c8d120c9a301
Create Date: 2026-10-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5f4a1e2b3c4"
down_revision: Union[str, Sequence[str], None] = "c8d120c9a301"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fraud_reports",
        sa.Column("scam_type", sa.String(length=50), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "transactions",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.alter_column("fraud_reports", "scam_type", server_default=None)
    op.alter_column("transactions", "created_at", server_default=None)


def downgrade() -> None:
    op.drop_column("transactions", "created_at")
    op.drop_column("fraud_reports", "scam_type")
