from io import StringIO
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = REPOSITORY_ROOT / "alembic.ini"


def test_migration_chain_has_one_head_and_generates_fresh_schema(monkeypatch):
    # Alembic runs in offline SQL mode below: it must not connect to this URL.
    # Use the clean database name to prove the environment override is honored.
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://adera_user:offline-test@localhost:5432/adera_dev_clean",
    )
    output = StringIO()
    config = Config(str(ALEMBIC_CONFIG), output_buffer=output)
    config.set_main_option("sqlalchemy.url", "sqlite:///wrong-target.sqlite")
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["7b8c9d0e1f2a"]

    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()

    assert config.get_main_option("sqlalchemy.url") == (
        "postgresql+psycopg2://adera_user:offline-test@localhost:5432/adera_dev_clean"
    )

    for table in {
        "users",
        "payment_accounts",
        "fraud_reports",
        "transactions",
        "risk_assessments",
        "alerts",
        "scam_cases",
        "account_relationships",
    }:
        assert f"CREATE TABLE {table}" in sql

    assert sql.count("scam_type VARCHAR(50) NOT NULL") == 1
    assert "ALTER TABLE scam_cases ADD COLUMN scam_type" not in sql
    assert "FOREIGN KEY(user_id) REFERENCES users (id)" in sql
    assert "FOREIGN KEY(source_account_id) REFERENCES payment_accounts (id)" in sql
    assert "FOREIGN KEY(target_account_id) REFERENCES payment_accounts (id)" in sql
    assert "FOREIGN KEY(risk_assessment_id) REFERENCES risk_assessments (id)" in sql
    assert "FOREIGN KEY(alert_id) REFERENCES alerts (id)" in sql
    assert "FOREIGN KEY(analyst_id) REFERENCES users (id)" in sql
