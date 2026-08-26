#!/usr/bin/env python3
"""Generate post-freeze descriptive RQ2 tables for MLReproMutate."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


RQ2_DIR = Path(__file__).resolve().parent
CORPUS_DIR = RQ2_DIR.parent
RESULTS_DIR = RQ2_DIR / "results"

# Reuse the canonical combined primary + D027 accounting.
sys.path.insert(0, str(CORPUS_DIR))
from final_accounting import AccountingError, build_case_table  # noqa: E402


class RQ2Error(RuntimeError):
    """RQ2 evidence is missing or inconsistent."""


EXPECTED_IDS = tuple(
    [f"B01-{n:02d}" for n in range(1, 11)]
    + [f"B02-{n:02d}" for n in range(1, 30)]
)

EXPECTED_COMBINED = {
    "n": 23,
    "killed": 2,
    "survived": 21,
}

EXPECTED_B02 = {
    "n": 15,
    "killed": 2,
    "survived": 13,
}

WORKFLOW_ORDER = (
    "upstream-test",
    "ci",
    "documented-validation",
    "documented-experiment",
    "documented-example",
)

ORACLE_ORDER = (
    "assertion",
    "metric-threshold",
    "reference-comparison",
    "completion-only",
)

CONTRAST_ORDER = (
    "substantive-oracle",
    "completion-only",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RQ2Error(f"cannot read {path}: {exc}") from exc

    rows: list[dict[str, Any]] = []

    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue

        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RQ2Error(
                f"{path}:{line_number}: invalid JSON: {exc}"
            ) from exc

        if not isinstance(value, dict):
            raise RQ2Error(
                f"{path}:{line_number}: expected JSON object"
            )

        rows.append(value)

    return rows


def validate_blind_frame(rows: list[dict[str, Any]]) -> None:
    if len(rows) != 39:
        raise RQ2Error(
            f"blind frame has {len(rows)} rows; expected 39"
        )

    ids = tuple(row.get("case_id") for row in rows)

    if ids != EXPECTED_IDS:
        raise RQ2Error(
            "blind frame IDs/order differ from "
            "B01-01..B01-10 + B02-01..B02-29"
        )

    if len(set(ids)) != 39:
        raise RQ2Error("blind frame case IDs are not unique")

    for row in rows:
        case_id = row["case_id"]

        if case_id.startswith("B01-"):
            if row.get("oracle_kind") is not None:
                raise RQ2Error(
                    f"{case_id}: B01 oracle_kind must remain null"
                )

        elif case_id.startswith("B02-"):
            if row.get("oracle_kind") not in ORACLE_ORDER:
                raise RQ2Error(
                    f"{case_id}: invalid or missing B02 oracle_kind"
                )


def is_meaningful(row: dict[str, Any]) -> bool:
    return (
        row["combined_evaluated"]
        and row["combined_semantic_status"]
        == "confirmed-non-equivalent"
        and row["combined_outcome"] in {"killed", "survived"}
    )


def join_frames(
    blind_rows: list[dict[str, Any]],
    accounting_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    accounting_by_id = {
        row["case_id"]: row for row in accounting_rows
    }

    if set(accounting_by_id) != set(EXPECTED_IDS):
        raise RQ2Error(
            "final_accounting does not contain exactly 39 expected cases"
        )

    joined: list[dict[str, Any]] = []

    for blind in blind_rows:
        case_id = blind["case_id"]
        account = accounting_by_id[case_id]

        if blind["repository"] != account["repository"]:
            raise RQ2Error(
                f"{case_id}: repository mismatch between "
                "blind frame and canonical accounting"
            )

        row = {
            **blind,
            "operator": account["operator"],
            "combined_result_source": account[
                "combined_result_source"
            ],
            "combined_evaluated": account[
                "combined_evaluated"
            ],
            "combined_outcome": account[
                "combined_outcome"
            ],
            "combined_semantic_status": account[
                "combined_semantic_status"
            ],
        }

        row["meaningful_detection_denominator"] = (
            is_meaningful(row)
        )

        joined.append(row)

    return joined


def validate_frozen_totals(
    joined: list[dict[str, Any]],
) -> None:
    meaningful = [
        row
        for row in joined
        if row["meaningful_detection_denominator"]
    ]

    counts = Counter(
        row["combined_outcome"] for row in meaningful
    )

    observed = {
        "n": len(meaningful),
        "killed": counts["killed"],
        "survived": counts["survived"],
    }

    if observed != EXPECTED_COMBINED:
        raise RQ2Error(
            "combined meaningful denominator differs from "
            f"frozen accounting: {observed}"
        )

    b02 = [
        row
        for row in meaningful
        if row["batch"] == "B02"
    ]

    counts_b02 = Counter(
        row["combined_outcome"] for row in b02
    )

    observed_b02 = {
        "n": len(b02),
        "killed": counts_b02["killed"],
        "survived": counts_b02["survived"],
    }

    if observed_b02 != EXPECTED_B02:
        raise RQ2Error(
            "B02 meaningful denominator differs from "
            f"frozen accounting: {observed_b02}"
        )


def summarize(
    rows: list[dict[str, Any]],
    field: str,
    order: tuple[str, ...],
) -> list[dict[str, Any]]:
    table: list[dict[str, Any]] = []

    for category in order:
        subset = [
            row
            for row in rows
            if row.get(field) == category
        ]

        counts = Counter(
            row["combined_outcome"] for row in subset
        )

        n = len(subset)
        killed = counts["killed"]
        survived = counts["survived"]

        detection_rate = killed / n if n else None

        table.append(
            {
                field: category,
                "evaluated_confirmed_non_equivalent": n,
                "killed": killed,
                "survived": survived,
                "detection_rate": detection_rate,
                "detection_percent": (
                    detection_rate * 100
                    if detection_rate is not None
                    else None
                ),
            }
        )

    return table


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        raise RQ2Error(f"refusing to write empty CSV: {path}")

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    text = "".join(
        json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n"
        for row in rows
    )

    path.write_text(text, encoding="utf-8")


def format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def markdown_table(
    rows: list[dict[str, Any]],
    category_field: str,
    category_label: str,
) -> str:
    lines = [
        (
            f"| {category_label} | "
            "Confirmed non-equivalent evaluated | "
            "KILLED | SURVIVED | Detection |"
        ),
        "|---|---:|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row[category_field]),
                    str(
                        row[
                            "evaluated_confirmed_non_equivalent"
                        ]
                    ),
                    str(row["killed"]),
                    str(row["survived"]),
                    format_percent(
                        row["detection_percent"]
                    ),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def main() -> None:
    blind_path = RQ2_DIR / "blind_case_evidence.jsonl"

    blind_rows = read_jsonl(blind_path)
    validate_blind_frame(blind_rows)

    try:
        accounting_rows = build_case_table(CORPUS_DIR)
    except AccountingError as exc:
        raise RQ2Error(
            f"canonical final accounting failed: {exc}"
        ) from exc

    joined = join_frames(
        blind_rows,
        accounting_rows,
    )

    validate_frozen_totals(joined)

    meaningful_all = [
        row
        for row in joined
        if row["meaningful_detection_denominator"]
    ]

    meaningful_b02 = [
        row
        for row in meaningful_all
        if row["batch"] == "B02"
    ]

    workflow_table = summarize(
        meaningful_all,
        "workflow_kind",
        WORKFLOW_ORDER,
    )

    oracle_table = summarize(
        meaningful_b02,
        "oracle_kind",
        ORACLE_ORDER,
    )

    contrast_table = summarize(
        meaningful_b02,
        "oracle_strength_derived",
        CONTRAST_ORDER,
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    write_jsonl(
        RESULTS_DIR / "rq2_joined_cases.jsonl",
        joined,
    )

    write_csv(
        RESULTS_DIR / "rq2_workflow_kind.csv",
        workflow_table,
    )

    write_csv(
        RESULTS_DIR / "rq2_b02_oracle_kind.csv",
        oracle_table,
    )

    write_csv(
        RESULTS_DIR / "rq2_b02_oracle_contrast.csv",
        contrast_table,
    )

    summary = {
        "combined_meaningful": EXPECTED_COMBINED,
        "b02_meaningful": EXPECTED_B02,
        "workflow_kind": workflow_table,
        "b02_oracle_kind": oracle_table,
        "b02_oracle_contrast": contrast_table,
    }

    (
        RESULTS_DIR / "rq2_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    results_md = f"""# RQ2 descriptive results

## Denominators

Combined confirmed non-equivalent evaluated mutations:

- N = 23
- KILLED = 2
- SURVIVED = 21

B02 confirmed non-equivalent evaluated mutations with prospective
oracle metadata:

- N = 15
- KILLED = 2
- SURVIVED = 13

## RQ2a — Detection by frozen workflow kind

{markdown_table(
    workflow_table,
    "workflow_kind",
    "Workflow kind",
)}

Workflow kind is categorical; no ordinal ranking is assumed.

## RQ2b — B02 detection by prospectively recorded oracle kind

{markdown_table(
    oracle_table,
    "oracle_kind",
    "Oracle kind",
)}

B01 is excluded from this primary oracle-kind analysis because
schema-v1 B01 did not prospectively record `oracle_kind`.

## RQ2c — B02 derived oracle contrast

{markdown_table(
    contrast_table,
    "oracle_strength_derived",
    "Oracle contrast",
)}

The binary contrast was frozen before outcome join:
`completion-only` versus `substantive-oracle`.

## Interpretation constraint

These are descriptive results from a small and uneven sample with
only two detected confirmed non-equivalent mutations.

They do not establish causal effects, population-wide differences,
or statistical superiority of one workflow/oracle category.
"""

    (
        RESULTS_DIR / "RQ2_RESULTS.md"
    ).write_text(
        results_md,
        encoding="utf-8",
    )

    print("RQ2 outcome join: OK")
    print(
        "combined meaningful: "
        "23 (KILLED=2, SURVIVED=21)"
    )
    print(
        "B02 meaningful: "
        "15 (KILLED=2, SURVIVED=13)"
    )

    print()
    print("RQ2a workflow kind:")

    for row in workflow_table:
        print(
            f"  {row['workflow_kind']}: "
            f"n={row['evaluated_confirmed_non_equivalent']}, "
            f"killed={row['killed']}, "
            f"survived={row['survived']}, "
            f"detection="
            f"{format_percent(row['detection_percent'])}"
        )

    print()
    print("RQ2b B02 oracle kind:")

    for row in oracle_table:
        print(
            f"  {row['oracle_kind']}: "
            f"n={row['evaluated_confirmed_non_equivalent']}, "
            f"killed={row['killed']}, "
            f"survived={row['survived']}, "
            f"detection="
            f"{format_percent(row['detection_percent'])}"
        )

    print()
    print("RQ2c B02 oracle contrast:")

    for row in contrast_table:
        print(
            f"  {row['oracle_strength_derived']}: "
            f"n={row['evaluated_confirmed_non_equivalent']}, "
            f"killed={row['killed']}, "
            f"survived={row['survived']}, "
            f"detection="
            f"{format_percent(row['detection_percent'])}"
        )

    print()
    print(f"results: {RESULTS_DIR}")


if __name__ == "__main__":
    try:
        main()
    except RQ2Error as exc:
        raise SystemExit(
            f"RQ2 analysis failed: {exc}"
        ) from exc