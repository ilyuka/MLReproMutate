import json
import re
import sys
from pathlib import Path
from typing import Any

OPERATORS = {
    "dependency-pin",
    "random-seed",
    "data-split",
    "cv-fold-count",
}

WORKFLOW_KINDS = {
    "upstream-test",
    "documented-validation",
    "documented-experiment",
    "documented-example",
    "ci",
}

ORACLE_KINDS = {
    "assertion",
    "metric-threshold",
    "reference-comparison",
    "completion-only",
}

SEMANTIC_VERIFICATION_STATUSES = {
    "confirmed-non-equivalent",
    "confirmed-equivalent",
    "unverified",
    "not-run",
}

SCREENING_STATUSES = {
    "eligible",
    "setup-failed",
    "no-applicable-mutation",
    "workflow-unavailable",
    "out-of-scope",
}

BASELINE_STATUSES = {
    "passed",
    "failed",
    "not-run",
}

MUTATION_STATUSES = {
    "evaluated",
    "not-evaluated",
}

OUTCOMES = {
    "killed",
    "survived",
    "invalid",
    "equivalent",
    "timeout",
    "error",
}

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def require_mapping(
    record: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    value = record.get(key)

    if not isinstance(value, dict):
        raise TypeError(
            f"{key!r} must be an object"
        )

    return value


def validate_record(
    record: dict[str, Any],
) -> None:
    required = {
        "schema_version",
        "repository",
        "revision",
        "operator",
        "research",
        "workflow",
        "screening",
        "baseline",
        "mutation",
    }

    missing = required - record.keys()

    if missing:
        raise ValueError(
            f"missing fields: {sorted(missing)}"
        )

    schema_version = record["schema_version"]

    if schema_version not in {1, 2}:
        raise ValueError(
            "schema_version must be 1 or 2"
        )

    if schema_version == 2:
        if record.get("protocol_version") != "2.0":
            raise ValueError(
                "schema version 2 requires protocol_version='2.0'"
            )

    repository = record["repository"]

    if (
        not isinstance(repository, str)
        or repository.count("/") != 1
    ):
        raise ValueError(
            "repository must use owner/name form"
        )

    revision = record["revision"]

    if (
        not isinstance(revision, str)
        or SHA_PATTERN.fullmatch(revision) is None
    ):
        raise ValueError(
            "revision must be a 40-character lowercase SHA"
        )

    if record["operator"] not in OPERATORS:
        raise ValueError(
            f"unknown operator: {record['operator']!r}"
        )

    research = require_mapping(
        record,
        "research",
    )

    if not isinstance(
        research.get("kind"),
        str,
    ):
        raise TypeError(
            "research.kind must be a string"
        )

    if not isinstance(
        research.get("reference"),
        str,
    ):
        raise TypeError(
            "research.reference must be a string"
        )

    workflow = require_mapping(
        record,
        "workflow",
    )

    if workflow.get("kind") not in WORKFLOW_KINDS:
        raise ValueError(
            f"unknown workflow kind: "
            f"{workflow.get('kind')!r}"
        )

    for key in ("command", "reference"):
        if not isinstance(
            workflow.get(key),
            str,
        ):
            raise TypeError(
                f"workflow.{key} must be a string"
            )

    if schema_version == 2:
        oracle_kind = workflow.get("oracle_kind")

        if oracle_kind not in ORACLE_KINDS:
            raise ValueError(
                f"unknown workflow oracle kind: {oracle_kind!r}"
            )

    screening = require_mapping(
        record,
        "screening",
    )

    screening_status = screening.get("status")

    if screening_status not in SCREENING_STATUSES:
        raise ValueError(
            f"unknown screening status: "
            f"{screening_status!r}"
        )

    if not isinstance(
        screening.get(
            "compatibility_retry_used"
        ),
        bool,
    ):
        raise TypeError(
            "screening.compatibility_retry_used "
            "must be boolean"
        )

    reason = screening.get("reason")

    if reason is not None and not isinstance(
        reason,
        str,
    ):
        raise ValueError(
            "screening.reason must be string or null"
        )

    baseline = require_mapping(
        record,
        "baseline",
    )

    baseline_status = baseline.get("status")

    if baseline_status not in BASELINE_STATUSES:
        raise ValueError(
            f"unknown baseline status: "
            f"{baseline_status!r}"
        )

    duration = baseline.get(
        "duration_seconds"
    )

    if duration is not None and (
        isinstance(duration, bool)
        or not isinstance(
            duration,
            int | float,
        )
        or duration < 0
    ):
        raise ValueError(
            "baseline.duration_seconds must be "
            "a non-negative number or null"
        )

    mutation = require_mapping(
        record,
        "mutation",
    )

    mutation_status = mutation.get("status")

    if mutation_status not in MUTATION_STATUSES:
        raise ValueError(
            f"unknown mutation status: "
            f"{mutation_status!r}"
        )

    candidate_index = mutation.get(
        "candidate_index"
    )

    if candidate_index is not None and (
        isinstance(candidate_index, bool)
        or not isinstance(
            candidate_index,
            int,
        )
        or candidate_index < 1
    ):
        raise ValueError(
            "mutation.candidate_index must be "
            "a positive integer or null"
        )

    outcome = mutation.get("outcome")

    if mutation_status == "evaluated":
        if baseline_status != "passed":
            raise ValueError(
                "evaluated mutation requires "
                "a passed baseline"
            )

        if screening_status != "eligible":
            raise ValueError(
                "evaluated mutation requires "
                "eligible screening status"
            )

        if outcome not in OUTCOMES:
            raise ValueError(
                "evaluated mutation requires "
                "a valid outcome"
            )

        if candidate_index is None:
            raise ValueError(
                "evaluated mutation requires "
                "candidate_index"
            )

        report_path = mutation.get(
            "report_path"
        )

        if not isinstance(
            report_path,
            str,
        ):
            raise ValueError(
                "evaluated mutation requires "
                "report_path"
            )

    else:
        if outcome is not None:
            raise ValueError(
                "non-evaluated mutation must "
                "have outcome=null"
            )

    if schema_version == 2:
        semantic = mutation.get("semantic_verification")

        if not isinstance(semantic, dict):
            raise TypeError(
                "schema version 2 requires "
                "mutation.semantic_verification object"
            )

        semantic_status = semantic.get("status")

        if semantic_status not in SEMANTIC_VERIFICATION_STATUSES:
            raise ValueError(
                f"unknown semantic verification status: "
                f"{semantic_status!r}"
            )

        for key in ("method", "evidence"):
            value = semantic.get(key)

            if value is not None and not isinstance(value, str):
                raise TypeError(
                    f"mutation.semantic_verification.{key} "
                    "must be string or null"
                )

        if mutation_status == "not-evaluated":
            if semantic_status != "not-run":
                raise ValueError(
                    "non-evaluated mutation requires "
                    "semantic verification status 'not-run'"
                )

        elif outcome == "survived":
            if semantic_status not in {
                "confirmed-non-equivalent",
                "unverified",
            }:
                raise ValueError(
                    "survived mutation requires semantic verification "
                    "status 'confirmed-non-equivalent' or 'unverified'"
                )

        elif outcome == "equivalent":
            if semantic_status != "confirmed-equivalent":
                raise ValueError(
                    "equivalent mutation requires semantic verification "
                    "status 'confirmed-equivalent'"
                )


def validate_file(path: Path) -> int:
    errors = 0
    records = 0

    for line_number, raw_line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):
        if not raw_line.strip():
            continue

        records += 1

        try:
            value = json.loads(raw_line)

            if not isinstance(value, dict):
                raise TypeError(
                    "record must be a JSON object"
                )

            validate_record(value)

        except (
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ) as exc:
            errors += 1
            print(
                f"{path}:{line_number}: {exc}",
                file=sys.stderr,
            )

    if errors:
        print(
            f"{errors} invalid screening "
            f"record(s)",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {records} screening record(s)"
    )
    return 0


def main() -> None:
    path = (
        Path(__file__).resolve().parent
        / "screening.jsonl"
    )

    raise SystemExit(
        validate_file(path)
    )


if __name__ == "__main__":
    main()
