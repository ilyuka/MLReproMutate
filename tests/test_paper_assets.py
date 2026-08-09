from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest

from benchmarks.corpus import generate_paper_assets as assets
from benchmarks.corpus.final_accounting import calculate


@pytest.fixture()
def generated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    table_dir = tmp_path / "paper" / "tables"
    figure_dir = tmp_path / "paper" / "figures"
    results_numbers = tmp_path / "paper" / "results_numbers.md"
    expected = (
        table_dir / "study_summary.csv", table_dir / "operator_results.csv",
        table_dir / "d027_restoration.csv", table_dir / "results_tables.md",
        table_dir / "results_tables.tex",
        figure_dir / "evaluability_primary_vs_combined.png",
        figure_dir / "evaluability_primary_vs_combined.pdf",
        figure_dir / "b02_outcomes_by_operator.png",
        figure_dir / "b02_outcomes_by_operator.pdf",
        figure_dir / "d027_restoration_accounting.png",
        figure_dir / "d027_restoration_accounting.pdf", results_numbers,
    )
    monkeypatch.setattr(assets, "ROOT", tmp_path)
    monkeypatch.setattr(assets, "TABLE_DIR", table_dir)
    monkeypatch.setattr(assets, "FIGURE_DIR", figure_dir)
    monkeypatch.setattr(assets, "RESULTS_NUMBERS", results_numbers)
    monkeypatch.setattr(assets, "EXPECTED_FILES", expected)

    def fake_figures(_result: dict) -> None:
        for path in expected:
            if path.suffix in {".png", ".pdf"}:
                path.write_bytes(b"deterministic test figure")

    monkeypatch.setattr(assets, "_figures", fake_figures)
    assets.generate()
    return tmp_path


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_expected_outputs_and_table_shapes(generated: Path) -> None:
    expected = {
        "paper/tables/study_summary.csv", "paper/tables/operator_results.csv",
        "paper/tables/d027_restoration.csv", "paper/tables/results_tables.md",
        "paper/tables/results_tables.tex", "paper/results_numbers.md",
        "paper/figures/evaluability_primary_vs_combined.png",
        "paper/figures/evaluability_primary_vs_combined.pdf",
        "paper/figures/b02_outcomes_by_operator.png",
        "paper/figures/b02_outcomes_by_operator.pdf",
        "paper/figures/d027_restoration_accounting.png",
        "paper/figures/d027_restoration_accounting.pdf",
    }
    assert all((generated / path).is_file() for path in expected)
    assert len(_rows(generated / "paper/tables/study_summary.csv")) == 2
    operators = _rows(generated / "paper/tables/operator_results.csv")
    assert [row["operator"] for row in operators] == list(assets.OPERATORS)


def test_frozen_accounting_values_and_no_missing_numeric_cells(generated: Path) -> None:
    study = _rows(generated / "paper/tables/study_summary.csv")
    assert [(row["evaluated"], row["selected"]) for row in study] == [("13", "39"), ("24", "39")]
    operators = _rows(generated / "paper/tables/operator_results.csv")
    for row in study + operators + _rows(generated / "paper/tables/d027_restoration.csv"):
        for key, value in row.items():
            if key not in {"layer", "operator", "state"}:
                assert value not in {"", "NaN", "nan"}
                float(value)
    result = calculate()
    assert (result["b02_primary"]["evaluated"], result["b02_primary"]["selected"]) == (6, 29)
    assert (result["b02_combined"]["evaluated"], result["b02_combined"]["selected"]) == (16, 29)
    assert tuple(result["combined"][key] for key in ("survived", "killed", "equivalent")) == (21, 2, 1)
    assert (result["confirmed_detection"]["killed"], result["confirmed_detection"]["denominator"]) == (2, 23)


def test_d027_exclusive_states_and_results_reference(generated: Path) -> None:
    d027 = _rows(generated / "paper/tables/d027_restoration.csv")
    counts = {row["state"]: int(row["count"]) for row in d027}
    exclusive = ("Mutation evaluated", "Not restored after substantive attempt",
                 "Report present, restoration not attempted", "No D027 report")
    assert sum(counts[state] for state in exclusive) == 24
    text = (generated / "paper/results_numbers.md").read_text(encoding="utf-8")
    for exact in ("13/39 (33.3%)", "24/39 (61.5%)", "6/29 (20.7%)",
                  "16/29 (55.2%)", "2/23 (8.7%)"):
        assert exact in text


def test_figures_nonempty_and_text_generation_deterministic(generated: Path,
                                                              monkeypatch: pytest.MonkeyPatch) -> None:
    figures = list((generated / "paper/figures").iterdir())
    assert len(figures) == 6
    assert all(path.stat().st_size > 0 for path in figures)
    text_files = sorted((generated / "paper/tables").iterdir()) + [generated / "paper/results_numbers.md"]
    before = {path: hashlib.sha256(path.read_bytes()).digest() for path in text_files}
    assets.generate()
    after = {path: hashlib.sha256(path.read_bytes()).digest() for path in text_files}
    assert before == after
