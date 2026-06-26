"""Run one unattended B02 case, then broker its trusted local commit."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from b02_harness import (
    DEFAULT_FRAME,
    DEFAULT_LEDGER,
    REQUIRED_AMENDED_RERUN_REPORTS,
    load_sampling_frame,
    next_unprocessed_case,
    processed_case_ids,
)

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / ".codex" / "b02-case-prompt.txt"
EXPECTED_PUSH_URL = "no_push://disabled"


def run_git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=check, capture_output=True, text=True
    )


def changed_paths(status: str) -> set[str]:
    """Parse ordinary modified/untracked porcelain entries, rejecting complex ones."""

    paths: set[str] = set()
    for entry in status.splitlines():
        if len(entry) < 4 or entry[2] != " ":
            raise ValueError(f"unsupported git status entry: {entry!r}")
        state, path = entry[:2], entry[3:]
        if state not in {" M", "M ", "??"} or " -> " in path:
            raise ValueError(f"unsupported git status entry: {entry!r}")
        paths.add(path)
    return paths


def expected_report(case_id: str, changed: set[str]) -> str:
    required = REQUIRED_AMENDED_RERUN_REPORTS.get(case_id)
    if required is not None:
        report = f"benchmarks/corpus/runs/{required}"
        if report not in changed:
            raise ValueError(f"{case_id} requires dedicated report {report}")
        return report

    prefix = f"benchmarks/corpus/runs/{case_id}-"
    reports = {path for path in changed if path.startswith(prefix) and path.endswith(".json")}
    if len(reports) != 1:
        raise ValueError(f"expected exactly one matching {case_id} run report")
    return reports.pop()


def validate_changed_file_allowlist(case_id: str, status: str) -> set[str]:
    changed = changed_paths(status)
    report = expected_report(case_id, changed)
    if case_id in REQUIRED_AMENDED_RERUN_REPORTS:
        allowed = {report}
    else:
        allowed = {"benchmarks/corpus/screening.jsonl", report}
    if changed != allowed:
        unexpected = sorted(changed - allowed)
        missing = sorted(allowed - changed)
        raise ValueError(f"empirical change allowlist failed; unexpected={unexpected}, missing={missing}")
    return allowed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_empirical_identity(
    case: dict[str, object], allowed: set[str], root: Path = ROOT
) -> None:
    report_name = next(path for path in allowed if path.endswith(".json"))
    report = json.loads((root / report_name).read_text(encoding="utf-8"))
    fields = ("case_id", "repository", "revision", "operator")
    for field in fields:
        if report.get(field) != case.get(field):
            raise ValueError(f"run report {field} does not match frozen case")

    if "benchmarks/corpus/screening.jsonl" not in allowed:
        return
    records = [
        json.loads(line)
        for line in (root / "benchmarks/corpus/screening.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    if not any(
        all(record.get(field) == case.get(field) for field in fields)
        for record in records
    ):
        raise ValueError("screening ledger lacks the frozen case identity")


def push_url() -> str:
    return run_git("config", "--get", "remote.origin.pushurl").stdout.strip()


def codex_command() -> list[str]:
    return [
        "codex", "exec", "-c",
        'approval_policy="never"', "--sandbox", "workspace-write",
        "--cd", str(ROOT), "--add-dir", "/home/ilya/.cache/mlrepromutate/b02",
        "--strict-config", "-c", "sandbox_workspace_write.network_access=true",
        "-c", f'sandbox_workspace_write.writable_roots=["{ROOT}","/home/ilya/.cache/mlrepromutate/b02"]',
        "-",
    ]


def broker(case: dict[str, object], frame_hash: str) -> None:
    case_id = str(case["case_id"])
    status = run_git("status", "--porcelain=v1", "--untracked-files=all").stdout
    allowed = validate_changed_file_allowlist(case_id, status)
    validate_empirical_identity(case, allowed)
    if sha256(DEFAULT_FRAME) != frame_hash:
        raise RuntimeError("sampling_frame.jsonl changed")
    if push_url() != EXPECTED_PUSH_URL:
        raise RuntimeError("origin push URL is not no_push://disabled")
    subprocess.run([sys.executable, str(DEFAULT_LEDGER.parent / "validate_screening.py")], cwd=ROOT, check=True)

    frame = load_sampling_frame()
    processed = processed_case_ids(frame)
    following = next_unprocessed_case(frame, processed)
    if case_id not in processed or (following and following["case_id"] == case_id):
        raise RuntimeError(f"harness did not advance past {case_id}")

    run_git("add", "--", *sorted(allowed))
    run_git("commit", "-m", f"benchmarks: record {case_id} unattended execution")
    if run_git("status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise RuntimeError("working tree is not clean after commit")


def main() -> None:
    if run_git("status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise SystemExit("working tree must be clean before unattended execution")
    frame_hash = sha256(DEFAULT_FRAME)
    frame = load_sampling_frame()
    case = next_unprocessed_case(frame, processed_case_ids(frame))
    if case is None:
        raise SystemExit("all B02 cases are already processed")
    with PROMPT.open("rb") as prompt:
        completed = subprocess.run(codex_command(), cwd=ROOT, stdin=prompt, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"Codex failed with status {completed.returncode}; no commit brokered")
    broker(case, frame_hash)


if __name__ == "__main__":
    main()
