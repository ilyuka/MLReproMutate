import json
import subprocess
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from mlrepromutate.engine.runner import ExecutionResult
from mlrepromutate.models import MutationResult
from mlrepromutate.operators.base import MutationOperator


def get_git_revision(path: Path) -> str | None:
    """Return the current Git revision for a repository."""

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "rev-parse",
                "HEAD",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    revision = result.stdout.strip()

    return revision or None


def get_package_version() -> str:
    """Return the installed MLReproMutate package version."""

    try:
        return version("mlrepromutate")
    except PackageNotFoundError:
        return "unknown"


def build_run_report(
    *,
    project_root: Path,
    validation_command: str,
    timeout_seconds: float,
    operator: MutationOperator,
    baseline: ExecutionResult,
    results: list[MutationResult],
    requirements_file: Path | None,
    dependency_mode: str,
) -> dict[str, Any]:
    """Build a machine-readable mutation run report."""

    framework_root = Path(__file__).resolve().parents[2]

    mutations: list[dict[str, Any]] = []

    for result in results:
        candidate = result.candidate

        mutations.append(
            {
                "operator": candidate.operator,
                "category": candidate.category,
                "target": str(candidate.target),
                "description": candidate.description,
                "candidate_metadata": candidate.metadata,
                "outcome": result.outcome.value,
                "duration_seconds": result.duration_seconds,
                "reason": result.reason,
                "result_metadata": result.metadata,
                "execution": {
                    "return_code": result.metadata.get("return_code"),
                    "stdout": result.metadata.get("stdout"),
                    "stderr": result.metadata.get("stderr"),
                },
            }
        )

    outcome_counts: dict[str, int] = {}

    for result in results:
        outcome = result.outcome.value
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "project": {
            "path": str(project_root),
            "git_revision": get_git_revision(project_root),
        },
        "framework": {
            "name": "MLReproMutate",
            "version": get_package_version(),
            "git_revision": get_git_revision(framework_root),
        },
        "validation": {
            "command": validation_command,
            "timeout_seconds": timeout_seconds,
            "baseline": {
                "return_code": baseline.return_code,
                "duration_seconds": baseline.duration_seconds,
                "timed_out": baseline.timed_out,
                "stdout": baseline.stdout,
                "stderr": baseline.stderr,
            },
        },
        "operator": {
            "name": operator.name,
            "category": operator.category,
            "dependency_mode": dependency_mode,
            "requirements_file": (
                str(requirements_file)
                if requirements_file is not None
                else None
            ),
        },
        "summary": {
            "candidates": len(results),
            "outcomes": outcome_counts,
        },
        "mutations": mutations,
    }


def write_run_report(
    output_path: Path,
    report: dict[str, Any],
) -> None:
    """Write a JSON run report."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )