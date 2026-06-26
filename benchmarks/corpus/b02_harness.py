"""Select the next unprocessed case from the frozen B02 sampling frame."""

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path(__file__).resolve().parent
DEFAULT_FRAME = CORPUS_ROOT / "sampling_frame.jsonl"
DEFAULT_LEDGER = CORPUS_ROOT / "screening.jsonl"
DEFAULT_RUNS = CORPUS_ROOT / "runs"

CASE_ID_RE = re.compile(r"^B02-(\d{2})$")
REPORT_CASE_ID_RE = re.compile(r"^(B02-\d{2})(?:-|\.json)")
IDENTITY_FIELDS = ("repository", "revision", "operator")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue

        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc

        if not isinstance(record, dict):
            raise TypeError(f"{path}:{line_number}: record must be an object")

        records.append(record)

    return records


def _case_id(record: dict[str, Any], source: str) -> str:
    case_id = record.get("case_id")

    if not isinstance(case_id, str) or CASE_ID_RE.fullmatch(case_id) is None:
        raise ValueError(f"{source}: malformed B02 case_id: {case_id!r}")

    return case_id


def load_sampling_frame(path: Path = DEFAULT_FRAME) -> list[dict[str, Any]]:
    """Load and validate the frozen B02 frame without changing its order."""

    records = _load_jsonl(path)
    observed_ids: list[str] = []

    for index, record in enumerate(records, start=1):
        source = f"{path}:{index}"
        case_id = _case_id(record, source)

        missing = [field for field in IDENTITY_FIELDS if not record.get(field)]
        if missing:
            raise ValueError(f"{source}: missing identity fields: {missing}")

        observed_ids.append(case_id)

    if len(observed_ids) != len(set(observed_ids)):
        raise ValueError("sampling frame contains duplicate case IDs")

    expected_ids = [f"B02-{index:02d}" for index in range(1, len(records) + 1)]
    if observed_ids != expected_ids:
        raise ValueError(
            "sampling frame case IDs must be sequential and in frozen order: "
            f"expected {expected_ids}, got {observed_ids}"
        )

    return records


def _identity(record: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(record.get(field) for field in IDENTITY_FIELDS)


def processed_case_ids(
    frame: Iterable[dict[str, Any]],
    ledger_path: Path = DEFAULT_LEDGER,
    runs_path: Path = DEFAULT_RUNS,
) -> set[str]:
    """Return B02 cases already represented by the ledger or run reports."""

    frame_records = list(frame)
    frame_ids = {_case_id(record, "sampling frame") for record in frame_records}
    identity_to_id = {_identity(record): record["case_id"] for record in frame_records}
    if len(identity_to_id) != len(frame_records):
        raise ValueError("sampling frame contains duplicate case identities")
    processed: set[str] = set()
    ledger_ids: set[str] = set()

    if ledger_path.exists():
        for index, record in enumerate(_load_jsonl(ledger_path), start=1):
            if "case_id" in record:
                case_id = _case_id(record, f"{ledger_path}:{index}")
                if case_id not in frame_ids:
                    raise ValueError(
                        f"{ledger_path}:{index}: B02 case_id is not in the frozen frame: "
                        f"{case_id}"
                    )
            else:
                case_id = identity_to_id.get(_identity(record))
                if case_id is None:
                    continue

            if case_id in ledger_ids:
                raise ValueError(f"screening ledger contains duplicate B02 case: {case_id}")

            ledger_ids.add(case_id)
            processed.add(case_id)

    if runs_path.exists():
        for report_path in sorted(runs_path.glob("B02*.json")):
            match = REPORT_CASE_ID_RE.match(report_path.name)
            if match is None:
                raise ValueError(f"malformed B02 report filename: {report_path.name}")

            case_id = match.group(1)
            if case_id not in frame_ids:
                raise ValueError(
                    f"B02 report case_id is not in the frozen frame: {case_id}"
                )
            processed.add(case_id)

    return processed


def next_unprocessed_case(
    frame: Iterable[dict[str, Any]],
    processed: set[str],
) -> dict[str, Any] | None:
    """Return the first frozen-order case not present in ``processed``."""

    for record in frame:
        if record["case_id"] not in processed:
            return record

    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Identify the next unprocessed frozen B02 case without executing it."
    )
    parser.add_argument("--sampling-frame", type=Path, default=DEFAULT_FRAME)
    parser.add_argument("--screening-ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    frame = load_sampling_frame(args.sampling_frame)
    processed = processed_case_ids(frame, args.screening_ledger, args.runs_dir)
    next_case = next_unprocessed_case(frame, processed)

    if next_case is None:
        print("No unprocessed B02 cases.")
    else:
        print(json.dumps(next_case, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
