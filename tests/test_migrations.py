from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_migration_chain_is_valid():
    config = Config(str(ROOT_DIR / "alembic.ini"))
    script = ScriptDirectory.from_config(config)

    initial = script.get_revision("e23588f3a510")
    application = script.get_revision("76f9e71a6602")
    restoration = script.get_revision("217e6c5990a5")
    latest = script.get_revision("939c36146b33")

    assert initial is not None
    assert application is not None
    assert restoration is not None
    assert latest is not None

    assert application.down_revision == initial.revision
    assert restoration.down_revision == application.revision
    assert latest.down_revision == restoration.revision
    assert script.get_current_head() == latest.revision


def test_application_migration_does_not_recreate_tables():
    migration = ROOT_DIR / (
        "migrations/versions/76f9e71a6602_create_application_tables.py"
    )

    source = migration.read_text()

    assert "def upgrade() -> None:\n    pass" in source
    assert "def downgrade() -> None:\n    pass" in source
