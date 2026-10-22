"""Validation checks for the Phase 0 baseline evidence artifacts."""

from pathlib import Path


LEDGER_ROOT = (
    Path(__file__).resolve().parents[1]
    / "openspec"
    / "changes"
    / "backend-frontend-replacement"
    / "ledger"
)


def test_api_ledger_covers_every_documented_api_route():
    ledger = (LEDGER_ROOT / "api-endpoints.md").read_text(encoding="utf-8")

    route_ids = [
        "API-001",
        "API-002",
        "API-003",
        "API-004",
        "API-005",
        "API-006",
        "API-007",
        "API-008",
        "API-009",
        "API-010",
        "API-011",
        "API-012",
        "API-013",
        "API-014",
        "API-015",
        "API-016",
        "API-017",
        "API-018",
        "API-019",
    ]

    assert all(route_id in ledger for route_id in route_ids)
    for field in (
        "Authentication",
        "Request schema",
        "Response schema",
        "Normalization",
        "Status/error",
        "Ordering",
        "Consumer",
        "Classification",
        "Evidence",
    ):
        assert f"{field}" in ledger


def test_phase_0_evidence_records_data_quality_and_release_gate():
    for filename in (
        "contract-fixtures.md",
        "data-invariants.md",
        "quality-baseline.md",
        "release-gate.md",
    ):
        assert (LEDGER_ROOT / filename).exists()

    quality = (LEDGER_ROOT / "quality-baseline.md").read_text(encoding="utf-8")
    assert "strict_tdd: false" in quality
    assert "workspace command" in quality.lower()

    invariants = (LEDGER_ROOT / "data-invariants.md").read_text(encoding="utf-8")
    assert "append-only" in invariants.lower()
    assert "stock_actual = stock_inicial + entradas - salidas" in invariants
