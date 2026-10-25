"""Pruebas estáticas de la configuración PostgreSQL de CI."""

from pathlib import Path
import re


CI_WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def test_ci_provisiona_postgresql_18_con_base_de_test_aislada():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "image: postgres:18" in workflow
    assert "POSTGRES_DB: nexus_test" in workflow
    assert "DATABASE_URL: postgresql://" in workflow
    assert "localhost:5432/nexus_test" in workflow


def test_ci_no_define_sqlite_y_migra_antes_de_ejecutar_pytest():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "sqlite:///" not in workflow
    migration = re.search(r"alembic(?:\s+-c\s+\S+)?\s+upgrade\s+head", workflow)
    pytest_run = re.search(r"(?:PYTHONPATH=\.\s+)?pytest\s+-v", workflow)

    assert migration is not None
    assert pytest_run is not None
    assert migration.start() < pytest_run.start()
