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
    "ci",
    "documented-validation",
    "documented-experiment",
    "documented-example",
}

ORACLE_KINDS = {
    "assertion",
    "metric-threshold",
    "reference-comparison",
    "completion-only",
}

REQUIRED = {
    "pool_index",
    "repository",
    "revision",
    "operator",
    "target",
    "candidate_evidence",
    "workflow_kind",
    "workflow_command",
    "workflow_reference",
    "oracle_kind",
    "research_reference",
    "selection_reason",
}

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
URL_RE = re.compile(r"^https?://")


def fail(message: str) -> None:
    raise ValueError(message)


def validate_record(
    row: dict[str, Any],
    expected_operator: str,
) -> None:
    missing = REQUIRED - row.keys()
    if missing:
        fail(f"missing fields: {sorted(missing)}")

    index = row["pool_index"]
    if isinstance(index, bool) or not isinstance(index, int) or index < 1:
        fail("pool_index must be a positive integer")

    repository = row["repository"]
    if (
        not isinstance(repository, str)
        or repository.count("/") != 1
    ):
        fail("repository must use owner/name form")

    revision = row["revision"]
    if (
        not isinstance(revision, str)
        or SHA_RE.fullmatch(revision) is None
    ):
        fail("revision must be a 40-character lowercase SHA")

    operator = row["operator"]
    if operator not in OPERATORS:
        fail(f"unknown operator: {operator!r}")

    if operator != expected_operator:
        fail(
            f"expected operator {expected_operator!r}, "
            f"got {operator!r}"
        )

    if operator == "dependency-pin":
        candidate_index = row.get("candidate_index")

        if (
            isinstance(candidate_index, bool)
            or not isinstance(candidate_index, int)
            or candidate_index < 1
        ):
            fail(
                "dependency-pin requires positive integer "
                "candidate_index"
            )

        evidence = row["candidate_evidence"]

        if "==" not in evidence or ">=" not in evidence:
            fail(
                "dependency-pin candidate_evidence must "
                "describe == -> >= mutation"
            )

    if operator == "data-split":
            candidate_index = row.get("candidate_index")

            if (
                isinstance(candidate_index, bool)
                or not isinstance(candidate_index, int)
                or candidate_index < 1
            ):
                fail(
                    "data-split requires positive integer "
                    "candidate_index"
                )

            evidence = row["candidate_evidence"]

            if "train_test_split" not in evidence:
                fail(
                    "data-split candidate_evidence must contain "
                    "train_test_split"
                )

            if "stratify=" not in evidence:
                fail(
                    "data-split candidate_evidence must contain "
                    "stratify"
                )

            if "stratify=None" not in evidence:
                fail(
                    "data-split candidate_evidence must describe "
                    "mutation to stratify=None"
                )

    if operator == "cv-fold-count":
            candidate_index = row.get("candidate_index")

            if (
                isinstance(candidate_index, bool)
                or not isinstance(candidate_index, int)
                or candidate_index < 1
            ):
                fail(
                    "cv-fold-count requires positive integer "
                    "candidate_index"
                )

            allowed_splitters = {
                "KFold",
                "StratifiedKFold",
                "RepeatedKFold",
                "RepeatedStratifiedKFold",
            }

            splitter = row.get("splitter_type")

            if splitter not in allowed_splitters:
                fail(
                    f"unsupported splitter_type: {splitter!r}"
                )

            original = row.get("original_n_splits")
            mutated = row.get("mutated_n_splits")

            if (
                isinstance(original, bool)
                or not isinstance(original, int)
                or original < 2
            ):
                fail(
                    "original_n_splits must be integer >= 2"
                )

            if (
                isinstance(mutated, bool)
                or not isinstance(mutated, int)
            ):
                fail(
                    "mutated_n_splits must be an integer"
                )

            if mutated != original + 1:
                fail(
                    "cv-fold-count requires mutated_n_splits "
                    "== original_n_splits + 1"
                )

            evidence = row["candidate_evidence"]

            if "n_splits=" not in evidence:
                fail(
                    "cv-fold-count candidate_evidence must "
                    "contain explicit n_splits="
                )

    if row["workflow_kind"] not in WORKFLOW_KINDS:
        fail(
            f"unknown workflow_kind: "
            f"{row['workflow_kind']!r}"
        )

    if row["oracle_kind"] not in ORACLE_KINDS:
        fail(
            f"unknown oracle_kind: "
            f"{row['oracle_kind']!r}"
        )

    for key in (
        "target",
        "candidate_evidence",
        "workflow_command",
        "workflow_reference",
        "selection_reason",
    ):
        value = row[key]
        if not isinstance(value, str) or not value.strip():
            fail(f"{key} must be a non-empty string")

    ref = row["research_reference"]
    if not isinstance(ref, str) or URL_RE.match(ref) is None:
        fail("research_reference must be a plain http(s) URL")

    if "[" in ref or "](" in ref:
        fail("research_reference must not contain Markdown")

    haystack = json.dumps(row).lower()

    forbidden = (
        "likely killed",
        "likely survived",
        "probably killed",
        "probably survived",
        "expected to be killed",
        "expected to survive",
    )

    for phrase in forbidden:
        if phrase in haystack:
            fail(
                f"outcome-prediction language found: {phrase!r}"
            )


def validate(path: Path) -> None:
    expected_operator = path.stem

    if expected_operator not in OPERATORS:
        fail(
            "pool filename must be one of "
            "dependency-pin.jsonl, random-seed.jsonl, "
            "data-split.jsonl, cv-fold-count.jsonl"
        )

    rows = []

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not line.strip():
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"line {line_number}: invalid JSON: {exc}")

        if not isinstance(value, dict):
            fail(f"line {line_number}: record must be an object")

        try:
            validate_record(value, expected_operator)
        except ValueError as exc:
            fail(f"line {line_number}: {exc}")

        rows.append(value)

    if not rows:
        fail("pool is empty")

    indexes = [row["pool_index"] for row in rows]
    expected_indexes = list(range(1, len(rows) + 1))

    if indexes != expected_indexes:
        fail(
            f"pool_index must be exactly 1..{len(rows)} "
            "in file order"
        )

    repositories = [row["repository"] for row in rows]

    duplicates = sorted(
        repo
        for repo in set(repositories)
        if repositories.count(repo) > 1
    )

    if duplicates:
        fail(
            f"duplicate repositories: {duplicates}"
        )

    print(f"OK: {len(rows)} pool records")
    print(f"operator: {expected_operator}")
    print(f"unique repositories: {len(set(repositories))}")

    oracle_counts: dict[str, int] = {}

    for row in rows:
        kind = row["oracle_kind"]
        oracle_counts[kind] = oracle_counts.get(kind, 0) + 1

    print("oracle kinds:")
    for kind in sorted(oracle_counts):
        print(f"  {kind}: {oracle_counts[kind]}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: validate_pool.py PATH"
        )

    path = Path(sys.argv[1])

    try:
        validate(path)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
