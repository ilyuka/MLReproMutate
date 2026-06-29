"""Run one unattended B02 case, then broker its trusted local commit."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from b02_harness import (
    D025_RECOVERY_SUFFIX,
    DEFAULT_FRAME,
    DEFAULT_LEDGER,
    REQUIRED_AMENDED_RERUN_REPORTS,
    d025_recoverable_cases,
    load_sampling_frame,
    next_unprocessed_case,
    processed_case_ids,
    recovery_work_dir,
    validate_d025_report,
)

ROOT = Path(__file__).resolve().parents[2]
PROMPT = ROOT / ".codex" / "b02-case-prompt.txt"
EXPECTED_PUSH_URL = "no_push://disabled"
D025_INSTRUCTIONS = """
D025 applies to every normal execution beginning at B02-21 and every targeted
recovery. Fixed ceilings: clone/checkout/base provisioning 300 seconds;
setup/install 1800; baseline validation 900; mutant validation 900; semantic
verification 300. After native documented setup, at most three intentional
corrections are allowed, each directed by a concrete prior failure: documented
historical-runtime provisioning (public archival channels allowed); compatible
version/range adjustment of a NON-TARGET dependency after demonstrated
packaging/interpreter/ABI/runtime incompatibility; installation of a concretely
missing runtime/test/validation dependency; or environment-only path/cache/HOME/
XDG/locale normalization without research-semantic change.
Record their classes respectively as historical-runtime-provisioning,
non-target-dependency-adjustment, missing-runtime-test-validation-dependency,
or environment-normalization.

Forbidden: source compatibility patches; candidate/workflow/oracle changes;
skipped validation; timeout increases; outcome-directed correction; a TARGET
dependency constraint that undoes the mutation; CPU substitution for genuinely
specialized-hardware-only workflow. Infrastructure failures consume no
correction and produce no canonical report or ledger change. Baseline and
mutant use independent environments and equivalent corrections when mutation
is evaluated. Add report provenance for D025 policy, primary/recovery mode,
prior report path for recovery, correction count and ordered descriptions,
reasons and prior failures, exact timeouts, frozen case identity, independent
environment paths, infrastructure_valid, mutation_evaluated, and correction
symmetry. Canonical ledger report_path values use benchmarks/corpus/runs/...
"""


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


def expected_report(case_id: str, changed: set[str], recovery: bool = False) -> str:
    if recovery:
        report = f"benchmarks/corpus/runs/{case_id}{D025_RECOVERY_SUFFIX}"
        if report not in changed:
            raise ValueError(f"{case_id} recovery requires dedicated report {report}")
        return report
    required = REQUIRED_AMENDED_RERUN_REPORTS.get(case_id)
    if required is not None:
        report = f"benchmarks/corpus/runs/{required}"
        if report not in changed:
            raise ValueError(f"{case_id} requires dedicated report {report}")
        return report

    prefix = f"benchmarks/corpus/runs/{case_id}-"
    reports = {
        path for path in changed if path.startswith(prefix) and path.endswith(".json")
    }
    if len(reports) != 1:
        raise ValueError(f"expected exactly one matching {case_id} run report")
    return reports.pop()


def validate_changed_file_allowlist(
    case_id: str, status: str, recovery: bool = False
) -> set[str]:
    changed = changed_paths(status)
    report = expected_report(case_id, changed, recovery)
    if case_id in REQUIRED_AMENDED_RERUN_REPORTS and not recovery:
        allowed = {report}
    else:
        allowed = {"benchmarks/corpus/screening.jsonl", report}
    if changed != allowed:
        unexpected = sorted(changed - allowed)
        missing = sorted(allowed - changed)
        raise ValueError(
            f"empirical change allowlist failed; unexpected={unexpected}, missing={missing}"
        )
    return allowed


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_empirical_identity(
    case: dict[str, object],
    allowed: set[str],
    root: Path = ROOT,
    recovery: bool = False,
) -> None:
    report_name = next(path for path in allowed if path.endswith(".json"))
    report = json.loads((root / report_name).read_text(encoding="utf-8"))
    if recovery or report.get("d025_policy") == "D025":
        validate_d025_report(report, case, recovery=recovery)
    if recovery:
        prior_name = report["prior_report_path"]
        prior = Path(prior_name)
        if (
            prior.is_absolute()
            or ".." in prior.parts
            or not prior.name.startswith(f"{case['case_id']}-")
            or prior_name in allowed
            or not (root / prior).is_file()
        ):
            raise ValueError(
                "D025 recovery prior report must be an unchanged case report"
            )
    fields = ("case_id", "repository", "revision", "operator")

    frozen_identity = report.get("frozen_case")
    if isinstance(frozen_identity, dict):
        report_identity = dict(frozen_identity)
        if report.get("case_id") is not None:
            report_identity["case_id"] = report["case_id"]
    else:
        report_identity = report

    for field in fields:
        if report_identity.get(field) != case.get(field):
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
    matches = [
        record
        for record in records
        if all(record.get(field) == case.get(field) for field in fields)
    ]
    if len(matches) != 1:
        raise ValueError("screening ledger lacks the frozen case identity")
    report_path = matches[0].get("mutation", {}).get("report_path")
    if (
        matches[0].get("mutation", {}).get("status") == "evaluated"
        and report_path != report_name
    ):
        raise ValueError(
            "canonical D025 report_path must use benchmarks/corpus/runs/... form"
        )


def push_url() -> str:
    return run_git("config", "--get", "remote.origin.pushurl").stdout.strip()


def codex_command() -> list[str]:
    return [
        "codex",
        "exec",
        "-c",
        'approval_policy="never"',
        "--sandbox",
        "workspace-write",
        "--cd",
        str(ROOT),
        "--add-dir",
        "/home/ilya/.cache/mlrepromutate/b02",
        "--strict-config",
        "-c",
        "sandbox_workspace_write.network_access=true",
        "-c",
        f'sandbox_workspace_write.writable_roots=["{ROOT}","/home/ilya/.cache/mlrepromutate/b02"]',
        "-",
    ]


def broker(case: dict[str, object], frame_hash: str, recovery: bool = False) -> None:
    case_id = str(case["case_id"])
    status = run_git("status", "--porcelain=v1", "--untracked-files=all").stdout
    allowed = validate_changed_file_allowlist(case_id, status, recovery)
    validate_empirical_identity(case, allowed, recovery=recovery)
    if sha256(DEFAULT_FRAME) != frame_hash:
        raise RuntimeError("sampling_frame.jsonl changed")
    if push_url() != EXPECTED_PUSH_URL:
        raise RuntimeError("origin push URL is not no_push://disabled")
    subprocess.run(
        [sys.executable, str(DEFAULT_LEDGER.parent / "validate_screening.py")],
        cwd=ROOT,
        check=True,
    )

    if not recovery:
        frame = load_sampling_frame()
        processed = processed_case_ids(frame)
        following = next_unprocessed_case(frame, processed)
        if case_id not in processed or (following and following["case_id"] == case_id):
            raise RuntimeError(f"harness did not advance past {case_id}")

    run_git("add", "--", *sorted(allowed))
    action = "D025 recovery" if recovery else "unattended execution"
    run_git("commit", "-m", f"benchmarks: record {case_id} {action}")
    if run_git("status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise RuntimeError("working tree is not clean after commit")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover", metavar="B02-NN")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if run_git("status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise SystemExit("working tree must be clean before unattended execution")
    frame_hash = sha256(DEFAULT_FRAME)
    frame = load_sampling_frame()
    recovery = args.recover is not None
    if recovery:
        choices = {case["case_id"]: case for case in d025_recoverable_cases(frame)}
        case = choices.get(args.recover)
        if case is None:
            raise SystemExit(f"{args.recover!r} is not D025-recoverable")
        work_dir = recovery_work_dir(args.recover)
        instructions = (
            PROMPT.read_text(encoding="utf-8")
            + D025_INSTRUCTIONS
            + (
                f"\nTargeted D025 recovery: execute exactly {args.recover}. Use the fresh unique "
                f"work directory {work_dir}. Preserve every old report. Write exactly "
                f"benchmarks/corpus/runs/{args.recover}{D025_RECOVERY_SUFFIX} and replace "
                "exactly the existing screening ledger line. If infrastructure is invalid, "
                "leave no canonical report or ledger change and exit nonzero.\n"
            )
        )
    else:
        case = next_unprocessed_case(frame, processed_case_ids(frame))
        if case is None:
            raise SystemExit("all B02 cases are already processed")
        instructions = PROMPT.read_text(encoding="utf-8") + D025_INSTRUCTIONS
    completed = subprocess.run(
        codex_command(), cwd=ROOT, input=instructions, text=True, check=False
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"Codex failed with status {completed.returncode}; no commit brokered"
        )
    broker(case, frame_hash, recovery=recovery)


if __name__ == "__main__":
    main()
