import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "benchmarks" / "corpus"

import sys

sys.path.insert(0, str(CORPUS))

from b02_unattended import validate_changed_file_allowlist, validate_empirical_identity


def test_changed_file_allowlist_accepts_normal_case() -> None:
    status = (
        " M benchmarks/corpus/screening.jsonl\n"
        "?? benchmarks/corpus/runs/B02-03-braindecode-seed.json\n"
    )
    assert validate_changed_file_allowlist("B02-03", status) == {
        "benchmarks/corpus/screening.jsonl",
        "benchmarks/corpus/runs/B02-03-braindecode-seed.json",
    }


def test_b02_01_requires_dedicated_amended_report() -> None:
    status = "?? benchmarks/corpus/runs/B02-01-amended-policy-rerun.json\n"
    assert validate_changed_file_allowlist("B02-01", status)


def test_unexpected_changed_file_stops_commit_brokerage() -> None:
    status = (
        " M benchmarks/corpus/screening.jsonl\n"
        "?? benchmarks/corpus/runs/B02-03-result.json\n"
        " M src/mlrepromutate/cli.py\n"
    )
    with pytest.raises(ValueError, match="unexpected=.*src/mlrepromutate/cli.py"):
        validate_changed_file_allowlist("B02-03", status)


def test_driver_contains_no_push_command() -> None:
    source = (CORPUS / "b02_unattended.py").read_text(encoding="utf-8")
    assert '"push"' not in source
    assert "'push'" not in source


def test_matching_report_and_screening_identity_are_accepted(tmp_path: Path) -> None:
    case = {
        "case_id": "B02-03",
        "repository": "owner/repo",
        "revision": "a" * 40,
        "operator": "random-seed",
    }
    runs = tmp_path / "benchmarks/corpus/runs"
    runs.mkdir(parents=True)
    report = runs / "B02-03-result.json"
    report.write_text(json.dumps(case), encoding="utf-8")
    ledger = tmp_path / "benchmarks/corpus/screening.jsonl"
    ledger.write_text(json.dumps(case) + "\n", encoding="utf-8")
    validate_empirical_identity(
        case,
        {
            "benchmarks/corpus/screening.jsonl",
            "benchmarks/corpus/runs/B02-03-result.json",
        },
        tmp_path,
    )
