"""Select B02 cases and run explicitly chosen commands with compact output."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from b02_isolation import run_isolated as run_in_candidate_sandbox

CORPUS_ROOT = Path(__file__).resolve().parent
DEFAULT_FRAME = CORPUS_ROOT / "sampling_frame.jsonl"
DEFAULT_LEDGER = CORPUS_ROOT / "screening.jsonl"
DEFAULT_RUNS = CORPUS_ROOT / "runs"
DEFAULT_TAIL_LINES = 40
MAX_TAIL_BYTES = 16 * 1024

# Prospective B02 execution amendment adopted before B02-03. Keep these classes
# separate even where they currently share a value so later reports identify the
# resource being bounded rather than relying on one ambiguous common timeout.
TIMEOUT_SECONDS_BY_CLASS = {
    "setup-install": 900.0,
    "clone-checkout-venv": 300.0,
    "baseline-validation": 300.0,
    "mutant-validation": 300.0,
    "semantic-verification": 300.0,
}

# B02-01 was censored solely by the superseded setup ceiling. Its original
# report remains immutable; this distinct report name is the completion marker
# for the required fresh amended-policy rerun.
REQUIRED_AMENDED_RERUN_REPORTS = {
    "B02-01": "B02-01-amended-policy-rerun.json",
}

CASE_ID_RE = re.compile(r"^B02-(\d{2})$")
REPORT_CASE_ID_RE = re.compile(r"^(B02-\d{2})(?:-|\.json)")
STAGE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
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
                raise ValueError(
                    f"screening ledger contains duplicate B02 case: {case_id}"
                )

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

    for case_id, report_name in REQUIRED_AMENDED_RERUN_REPORTS.items():
        if case_id in frame_ids and not (runs_path / report_name).is_file():
            processed.discard(case_id)

    return processed


def timeout_for_class(timeout_class: str) -> float:
    """Return the prospectively fixed timeout for an explicit stage class."""

    try:
        return TIMEOUT_SECONDS_BY_CLASS[timeout_class]
    except KeyError as exc:
        known = ", ".join(TIMEOUT_SECONDS_BY_CLASS)
        raise ValueError(
            f"unknown B02 timeout class {timeout_class!r}; expected one of: {known}"
        ) from exc


def next_unprocessed_case(
    frame: Iterable[dict[str, Any]],
    processed: set[str],
) -> dict[str, Any] | None:
    """Return the first frozen-order case not present in ``processed``."""

    for record in frame:
        if record["case_id"] not in processed:
            return record

    return None


def b02_work_root() -> Path:
    """Return the fixed persistent candidate work root."""

    return Path("/home/ilya/.cache/mlrepromutate/b02")


def case_work_dir(case_id: str, work_root: Path | None = None) -> Path:
    """Return the deterministic work directory for a syntactically valid case."""

    if CASE_ID_RE.fullmatch(case_id) is None:
        raise ValueError(f"malformed B02 case_id: {case_id!r}")
    root = b02_work_root() if work_root is None else work_root.expanduser().resolve()
    return root / case_id


def _tail(path: Path, line_limit: int = DEFAULT_TAIL_LINES) -> tuple[list[str], bool]:
    size = path.stat().st_size
    with path.open("rb") as stream:
        if size > MAX_TAIL_BYTES:
            stream.seek(-MAX_TAIL_BYTES, os.SEEK_END)
        data = stream.read(MAX_TAIL_BYTES)

    lines = data.decode("utf-8", errors="replace").splitlines()
    truncated = size > len(data) or len(lines) > line_limit
    return lines[-line_limit:], truncated


def run_candidate_command(
    case_id: str,
    stage: str,
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    work_root: Path | None = None,
    tail_lines: int = DEFAULT_TAIL_LINES,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Run candidate argv via bubblewrap and persist a compact stage summary."""

    if not command or not all(isinstance(argument, str) for argument in command):
        raise ValueError("command must be a non-empty argv list of strings")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be greater than zero")
    if tail_lines <= 0:
        raise ValueError("tail_lines must be greater than zero")
    if STAGE_RE.fullmatch(stage) is None:
        raise ValueError(f"invalid stage name: {stage!r}")

    resolved_cwd = cwd.expanduser().resolve()
    if not resolved_cwd.exists():
        raise FileNotFoundError(f"working directory does not exist: {resolved_cwd}")
    if not resolved_cwd.is_dir():
        raise NotADirectoryError(
            f"working directory is not a directory: {resolved_cwd}"
        )

    stage_dir = case_work_dir(case_id, work_root) / "stages" / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = stage_dir / "stdout.log"
    stderr_path = stage_dir / "stderr.log"
    summary_path = stage_dir / "summary.json"

    started = time.monotonic()
    timed_out = False
    return_code: int | None = None
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = run_in_candidate_sandbox(
                command,
                cwd=resolved_cwd,
                environment=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout_seconds,
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True

    duration_seconds = time.monotonic() - started
    stdout_tail, stdout_truncated = _tail(stdout_path, tail_lines)
    stderr_tail, stderr_truncated = _tail(stderr_path, tail_lines)
    summary: dict[str, Any] = {
        "case_id": case_id,
        "stage": stage,
        "command": list(command),
        "environment": dict(environment or {}),
        "cwd": str(resolved_cwd),
        "timeout_seconds": timeout_seconds,
        "duration_seconds": duration_seconds,
        "return_code": return_code,
        "timed_out": timed_out,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "stdout_tail_truncated": stdout_truncated,
        "stderr_tail_truncated": stderr_truncated,
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _require_frame_case(frame: Iterable[dict[str, Any]], case_id: str) -> None:
    if not any(record["case_id"] == case_id for record in frame):
        raise ValueError(f"case_id is not in the frozen sampling frame: {case_id}")


def status_for_case(case_id: str, work_root: Path | None = None) -> dict[str, Any]:
    """Return compact persisted execution summaries for one case."""

    case_dir = case_work_dir(case_id, work_root)
    summaries = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((case_dir / "stages").glob("*/summary.json"))
    ]
    return {"case_id": case_id, "work_dir": str(case_dir), "stages": summaries}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect frozen B02 cases and run explicit local argv commands."
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    next_parser = subparsers.add_parser("next")
    next_parser.add_argument("--sampling-frame", type=Path, default=DEFAULT_FRAME)
    next_parser.add_argument("--screening-ledger", type=Path, default=DEFAULT_LEDGER)
    next_parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("case_id")
    status_parser.add_argument("--sampling-frame", type=Path, default=DEFAULT_FRAME)
    status_parser.add_argument("--work-root", type=Path)

    run_parser = subparsers.add_parser("run-isolated")
    run_parser.add_argument("case_id")
    run_parser.add_argument("--stage", required=True)
    run_parser.add_argument(
        "--timeout-class",
        required=True,
        choices=tuple(TIMEOUT_SECONDS_BY_CLASS),
    )
    run_parser.add_argument("--cwd", required=True, type=Path)
    run_parser.add_argument("--tail-lines", type=int, default=DEFAULT_TAIL_LINES)
    run_parser.add_argument("--sampling-frame", type=Path, default=DEFAULT_FRAME)
    run_parser.add_argument("--work-root", type=Path)
    run_parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
    )
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> None:
    arguments = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(arguments or ["next"])
    frame = load_sampling_frame(args.sampling_frame)

    if args.action == "next":
        processed = processed_case_ids(frame, args.screening_ledger, args.runs_dir)
        next_case = next_unprocessed_case(frame, processed)
        print(json.dumps(next_case, ensure_ascii=False, sort_keys=True))
        return

    _require_frame_case(frame, args.case_id)
    if args.action == "status":
        result = status_for_case(args.case_id, args.work_root)
    else:
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        from b02_isolation import parse_environment

        result = run_candidate_command(
            args.case_id,
            args.stage,
            command,
            args.cwd,
            timeout_for_class(args.timeout_class),
            args.work_root,
            args.tail_lines,
            parse_environment(args.env),
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
