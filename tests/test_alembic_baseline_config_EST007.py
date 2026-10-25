"""Pruebas de selección explícita de la configuración baseline."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_config_apunta_a_una_raiz_separada() -> None:
    config = (ROOT / "alembic-baseline.ini").read_text(encoding="utf-8")

    assert "script_location = %(here)s/alembic_baseline" in config
    assert "script_location = %(here)s/alembic\n" not in config


def test_baseline_history_expone_una_raiz_y_la_historica_separadamente() -> None:
    baseline = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic-baseline.ini", "history"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    historical = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "alembic.ini", "history"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "000000000001" in baseline.stdout
    assert "a1b2c3d4e5f6" in historical.stdout


def test_ci_selecciona_baseline_antes_de_las_pruebas() -> None:
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "alembic -c alembic-baseline.ini upgrade head" in ci


def test_baseline_upgrade_offline_registra_la_revision() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic-baseline.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "INSERT INTO alembic_version" in result.stdout
    assert "000000000001" in result.stdout
