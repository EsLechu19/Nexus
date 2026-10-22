"""Validation checks for the T0.1 baseline ledger artifacts."""

from pathlib import Path


LEDGER_ROOT = (
    Path(__file__).resolve().parents[1]
    / "openspec"
    / "changes"
    / "backend-frontend-replacement"
    / "ledger"
)


def test_ledger_template_defines_required_evidence_fields_and_classifications():
    template = (LEDGER_ROOT / "entry-template.md").read_text(encoding="utf-8")

    for field in (
        "Endpoint",
        "Data",
        "Quality",
        "Deviation",
        "Decision",
        "Evidence",
        "Affected slice",
        "Rollback",
    ):
        assert f"| {field} |" in template

    for classification in (
        "documented contract",
        "observed behavior",
        "deviation",
        "assumption",
        "dependency",
        "open decision",
    ):
        assert f"`{classification}`" in template


def test_ledger_readme_defines_revision_convention_and_release_gate():
    readme = (LEDGER_ROOT / "README.md").read_text(encoding="utf-8")
    gate = (LEDGER_ROOT / "release-gate.md").read_text(encoding="utf-8")

    assert "BL-YYYYMMDD-NN" in readme
    assert "baseline revision" in readme.lower()
    assert "Release gate" in gate
    assert "rollback" in gate.lower()
