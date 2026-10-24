"""batch4 alert case decision

Revision ID: 7b8c9d0e1f2a
Revises: f1a2b3c4d5e6
Create Date: 2026-10-03 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7b8c9d0e1f2a"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("risk_assessment_id", sa.Integer(), nullable=True))
    op.add_column("alerts", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.alter_column("alerts", "created_at", server_default=None)
    op.create_foreign_key(
        "fk_alerts_risk_assessment_id_risk_assessments",
        "alerts",
        "risk_assessments",
        ["risk_assessment_id"],
        ["id"],
    )

    op.add_column("scam_cases", sa.Column("alert_id", sa.Integer(), nullable=True))
    op.add_column("scam_cases", sa.Column("analyst_id", sa.Integer(), nullable=True))
    op.add_column("scam_cases", sa.Column("decision", sa.String(length=30), nullable=True))
    op.add_column("scam_cases", sa.Column("decision_notes", sa.Text(), nullable=True))
    op.add_column("scam_cases", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
    op.alter_column("scam_cases", "created_at", server_default=None)
    op.create_foreign_key(
        "fk_scam_cases_alert_id_alerts",
        "scam_cases",
        "alerts",
        ["alert_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_scam_cases_analyst_id_users",
        "scam_cases",
        "users",
        ["analyst_id"],
        ["id"],
    )



def downgrade() -> None:
    op.drop_constraint("fk_scam_cases_analyst_id_users", "scam_cases", type_="foreignkey")
    op.drop_constraint("fk_scam_cases_alert_id_alerts", "scam_cases", type_="foreignkey")
    op.drop_column("scam_cases", "created_at")
    op.drop_column("scam_cases", "decision_notes")
    op.drop_column("scam_cases", "decision")
    op.drop_column("scam_cases", "analyst_id")
    op.drop_column("scam_cases", "alert_id")
    op.drop_constraint("fk_alerts_risk_assessment_id_risk_assessments", "alerts", type_="foreignkey")
    op.drop_column("alerts", "created_at")
    op.drop_column("alerts", "risk_assessment_id")
