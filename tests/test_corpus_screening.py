import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "benchmarks"
    / "corpus"
    / "validate_screening.py"
)

SPEC = importlib.util.spec_from_file_location(
    "validate_screening",
    VALIDATOR_PATH,
)

assert SPEC is not None
assert SPEC.loader is not None

MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

validate_record = MODULE.validate_record


def valid_record() -> dict:
    return {
        "schema_version": 1,
        "repository": "owner/repository",
        "revision": "a" * 40,
        "operator": "random-seed",
        "research": {
            "kind": "paper",
            "reference": "https://doi.org/example",
        },
        "workflow": {
            "kind": "documented-example",
            "command": "python example.py",
            "reference": "README.md",
        },
        "screening": {
            "status": "eligible",
            "reason": None,
            "compatibility_retry_used": False,
        },
        "baseline": {
            "status": "passed",
            "duration_seconds": 1.5,
        },
        "mutation": {
            "status": "evaluated",
            "candidate_index": 1,
            "outcome": "survived",
            "report_path": "runs/result.json",
        },
    }


def test_valid_screening_record() -> None:
    validate_record(valid_record())


def test_failed_baseline_cannot_have_evaluated_mutation() -> None:
    record = valid_record()

    record["baseline"]["status"] = "failed"

    try:
        validate_record(record)
    except ValueError as exc:
        assert "passed baseline" in str(exc)
    else:
        raise AssertionError(
            "Expected invalid screening record"
        )


def test_non_evaluated_record_has_no_outcome() -> None:
    record = valid_record()

    record["screening"]["status"] = "setup-failed"
    record["screening"]["reason"] = "dependency drift"
    record["baseline"]["status"] = "failed"
    record["mutation"] = {
        "status": "not-evaluated",
        "candidate_index": None,
        "outcome": None,
        "report_path": None,
    }

    validate_record(record)
