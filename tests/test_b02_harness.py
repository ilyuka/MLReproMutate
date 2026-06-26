import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "benchmarks" / "corpus" / "b02_harness.py"
FRAME_PATH = ROOT / "benchmarks" / "corpus" / "sampling_frame.jsonl"

SPEC = importlib.util.spec_from_file_location("b02_harness", HARNESS_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

load_sampling_frame = MODULE.load_sampling_frame
next_unprocessed_case = MODULE.next_unprocessed_case
processed_case_ids = MODULE.processed_case_ids


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def small_frame() -> list[dict]:
    return [
        {
            "case_id": f"B02-{index:02d}",
            "repository": f"owner/repository-{index}",
            "revision": str(index) * 40,
            "operator": "random-seed",
        }
        for index in range(1, 4)
    ]


def test_loads_all_frozen_cases_in_case_id_order() -> None:
    frame = load_sampling_frame(FRAME_PATH)

    assert len(frame) == 29
    assert [record["case_id"] for record in frame] == [
        f"B02-{index:02d}" for index in range(1, 30)
    ]


def test_detects_processed_cases_from_ledger_identity_and_report(
    tmp_path: Path,
) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    runs = tmp_path / "runs"
    runs.mkdir()
    legacy_record = dict(frame[0])
    legacy_record.pop("case_id")
    write_jsonl(ledger, [legacy_record, frame[1]])
    (runs / "B02-03-result.json").write_text("{}\n", encoding="utf-8")

    assert processed_case_ids(frame, ledger, runs) == {
        "B02-01",
        "B02-02",
        "B02-03",
    }


def test_chooses_first_unprocessed_case() -> None:
    frame = small_frame()

    assert next_unprocessed_case(frame, {"B02-01"}) == frame[1]


def test_returns_none_when_all_cases_are_processed() -> None:
    frame = small_frame()

    assert next_unprocessed_case(
        frame,
        {record["case_id"] for record in frame},
    ) is None


@pytest.mark.parametrize(
    "case_ids",
    [
        ["B02-01", "B02-01"],
        ["B02-01", "B2-02"],
        ["B02-02", "B02-01"],
    ],
)
def test_rejects_duplicate_malformed_or_out_of_order_frame_ids(
    tmp_path: Path,
    case_ids: list[str],
) -> None:
    records = small_frame()[:2]
    for record, case_id in zip(records, case_ids, strict=True):
        record["case_id"] = case_id
    frame_path = tmp_path / "sampling_frame.jsonl"
    write_jsonl(frame_path, records)

    with pytest.raises(ValueError):
        load_sampling_frame(frame_path)


def test_rejects_duplicate_processed_case_in_ledger(tmp_path: Path) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    write_jsonl(ledger, [frame[0], frame[0]])

    with pytest.raises(ValueError, match="duplicate B02 case"):
        processed_case_ids(frame, ledger, tmp_path / "missing-runs")


def test_rejects_malformed_case_id_in_ledger(tmp_path: Path) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    write_jsonl(ledger, [{**frame[0], "case_id": None}])

    with pytest.raises(ValueError, match="malformed B02 case_id"):
        processed_case_ids(frame, ledger, tmp_path / "missing-runs")
