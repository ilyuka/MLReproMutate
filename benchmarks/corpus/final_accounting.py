#!/usr/bin/env python3
"""Reproducible final accounting for the completed B01/B02 study.

The screening ledger identifies the canonical primary report (and therefore
resolves amended/corrective reports).  D027 reports are a secondary layer and
are used only when the canonical primary mutation was not evaluated.  S1 and
legacy reports are never discovered heuristically and cannot enter the table.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

CORPUS_DIR = Path(__file__).resolve().parent
RUNS_DIR = CORPUS_DIR / "runs"
CASE_FIELDS = (
    "case_id", "batch", "operator", "repository", "primary_status",
    "primary_evaluated", "primary_outcome", "primary_semantic_status",
    "d027_report_present", "d027_assessment_status", "d027_restored",
    "d027_evaluated", "d027_outcome", "d027_semantic_status",
    "combined_result_source", "combined_evaluated", "combined_outcome",
    "combined_semantic_status",
)
EXPECTED_IDS = tuple(
    [f"B01-{number:02d}" for number in range(1, 11)]
    + [f"B02-{number:02d}" for number in range(1, 30)]
)
EXPECTED = {
    "b02_primary": {"selected": 29, "evaluated": 6, "survived": 4,
                    "killed": 1, "equivalent": 1, "setup-failed": 21,
                    "workflow-unavailable": 2},
    "b02_combined": {"selected": 29, "evaluated": 16,
                     "non-evaluable": 13, "survived": 13, "killed": 2,
                     "equivalent": 1},
    "b01_primary": {"selected": 10, "evaluated": 7, "survived": 7,
                    "killed": 0},
    "b01_combined": {"selected": 10, "evaluated": 8,
                     "non-evaluable": 2, "survived": 8, "killed": 0},
    "combined": {"selected": 39, "evaluated": 24, "non-evaluable": 15,
                 "survived": 21, "killed": 2, "equivalent": 1},
}
EXPECTED_OPERATORS = {
    "random-seed": {"selected": 10, "evaluated": 5, "survived": 5,
                    "non-evaluable": 5},
    "dependency-pin": {"selected": 10, "evaluated": 4, "killed": 2,
                       "survived": 1, "equivalent": 1, "non-evaluable": 6},
    "data-split": {"selected": 6, "evaluated": 4, "survived": 4,
                   "non-evaluable": 2},
    "cv-fold-count": {"selected": 3, "evaluated": 3, "survived": 3,
                      "non-evaluable": 0},
}


class AccountingError(RuntimeError):
    """Structured evidence is missing, contradictory, or unexpected."""


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AccountingError(f"cannot read structured evidence {path}: {exc}") from exc


def _jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise AccountingError(f"cannot read structured evidence {path}: {exc}") from exc


def _lower(value: Any) -> str | None:
    return value.lower() if isinstance(value, str) else None


def _report_path(value: str) -> Path:
    path = Path(value)
    if path.parts[:2] == ("benchmarks", "corpus"):
        path = Path(*path.parts[2:])
    return CORPUS_DIR / path


def _case_identity(record: dict[str, Any]) -> tuple[str, str, str]:
    frozen = record.get("frozen_case", record)
    return frozen["repository"], frozen["revision"], frozen["operator"]


def _b01_ids(screening: list[dict[str, Any]], cohort: list[dict[str, Any]]) -> list[str]:
    """Recover calibration IDs from structured report/cohort identities.

    Schema-v1 screening predates ``case_id``: its first ten records are the
    frozen calibration sequence B01-01..B01-10.  D027 cohort identities and
    canonical report paths are used as independent structured cross-checks;
    neither outcomes nor current git state participate in the mapping.
    """
    identities: dict[tuple[str, str, str], str] = {}
    for item in cohort:
        identity = (item["repository"], item["revision"], item["operator"])
        identities[identity] = item["case_id"]
    result = []
    for number, row in enumerate(screening[:10], 1):
        expected = f"B01-{number:02d}"
        report = row["mutation"].get("report_path")
        if report:
            data = _json(_report_path(report))
            case_id = data.get("case_id")
            if case_id and case_id != expected:
                raise AccountingError(f"{expected}: canonical report says case_id={case_id}")
            if expected not in Path(report).name:
                raise AccountingError(f"{expected}: canonical report path does not identify its B01 row")
        else:
            case_id = identities.get(_case_identity(row))
            if case_id != expected:
                raise AccountingError(f"{expected}: D027 cohort identity maps to {case_id!r}")
        result.append(expected)
    return result


def _primary_semantic(row: dict[str, Any], report: dict[str, Any] | None) -> str:
    mutation = row["mutation"]
    semantic = mutation.get("semantic_verification") or {}
    status = _lower(semantic.get("status"))
    if status:
        return status
    if report:
        report_mutation = report.get("mutation", {})
        semantic = report_mutation.get("semantic_verification") or report.get("semantic_verification") or {}
        status = _lower(semantic.get("status") or report_mutation.get("semantic_status"))
        if status:
            return status
    # B01 schema v1 predates the explicit field. Its completed run reports
    # record an applied, concrete mutation and the frozen final-study accounting
    # treats those evaluated non-equivalent outcomes as confirmed. This explicit
    # compatibility rule is limited to schema v1; it never upgrades v2 evidence.
    if row.get("schema_version") == 1 and mutation["status"] == "evaluated":
        return "confirmed-non-equivalent"
    return "unverified" if mutation["status"] == "evaluated" else "not-run"


def _validate_primary_report(case_id: str, row: dict[str, Any], report: dict[str, Any]) -> None:
    report_case = report.get("case_id") or report.get("frozen_case", {}).get("case_id")
    if report_case and report_case != case_id:
        raise AccountingError(f"{case_id}: canonical report says case_id={report_case}")
    mutation = report.get("mutation")
    if not isinstance(mutation, dict):
        return  # Legacy runner report; canonical ledger supplies its classification.
    report_status = _lower(mutation.get("status"))
    report_outcome = _lower(mutation.get("outcome"))
    if report_status and report_status != row["mutation"]["status"]:
        raise AccountingError(f"{case_id}: screening/report mutation status contradiction")
    if report_outcome != _lower(row["mutation"].get("outcome")):
        raise AccountingError(f"{case_id}: screening/report mutation outcome contradiction")
    screening = report.get("screening", {})
    if screening.get("status") and screening["status"] != row["screening"]["status"]:
        raise AccountingError(f"{case_id}: screening/report primary status contradiction")


def _d027_fields(report: dict[str, Any] | None) -> dict[str, Any]:
    if report is None:
        return {"d027_report_present": False, "d027_assessment_status": "not-assessed",
                "d027_restored": False, "d027_evaluated": False,
                "d027_outcome": None, "d027_semantic_status": "not-run"}
    classification = report.get("d027_classification", {})
    d027 = report.get("d027", {})
    restoration = report.get("restoration", {})
    assessment = (
        classification.get("restoration") or restoration.get("status")
        or d027.get("restoration_classification")
    )
    if not assessment:
        raise AccountingError(f"{report.get('case_id')}: D027 assessment status missing")
    assessment = _lower(assessment)
    mutation = report.get("mutation", {})
    result = report.get("d027_result", {})
    evaluation = report.get("mutation_evaluation", {})
    outcome = _lower(
        classification.get("mutation_outcome") or mutation.get("outcome")
        or result.get("outcome") or evaluation.get("outcome")
        or report.get("final_d027_result")
    )
    evaluated = outcome in {"killed", "survived", "equivalent", "invalid", "timeout", "error"}
    explicit_evaluated = result.get("evaluated")
    if explicit_evaluated is False and evaluated:
        raise AccountingError(f"{report.get('case_id')}: contradictory D027 evaluated evidence")
    semantic = _lower(
        classification.get("semantic_status") or mutation.get("semantic_status")
        or (mutation.get("semantic_verification") or {}).get("status")
        or result.get("semantic_status")
        or (report.get("semantic_verification") or {}).get("status")
    ) or "not-run"
    restored = assessment == "restored"
    if evaluated and not restored:
        raise AccountingError(f"{report.get('case_id')}: evaluated D027 result is not restored")
    return {"d027_report_present": True, "d027_assessment_status": assessment,
            "d027_restored": restored, "d027_evaluated": evaluated,
            "d027_outcome": outcome, "d027_semantic_status": semantic}


def build_case_table(corpus_dir: Path = CORPUS_DIR) -> list[dict[str, Any]]:
    """Return the deterministic 39-row canonical-primary-plus-D027 table."""
    global CORPUS_DIR, RUNS_DIR
    old_corpus, old_runs = CORPUS_DIR, RUNS_DIR
    CORPUS_DIR, RUNS_DIR = corpus_dir, corpus_dir / "runs"
    try:
        screening = _jsonl(corpus_dir / "screening.jsonl")
        cohort = _jsonl(corpus_dir / "d027_restoration_cohort.jsonl")
        if len(screening) != 39:
            raise AccountingError(f"screening ledger has {len(screening)} rows, expected 39")
        if len(cohort) != 24 or len({item["case_id"] for item in cohort}) != 24:
            raise AccountingError("D027 cohort must contain exactly 24 unique cases")
        ids = _b01_ids(screening, cohort) + [item.get("case_id") for item in screening[10:]]
        if tuple(ids) != EXPECTED_IDS:
            raise AccountingError(f"intended case IDs differ: observed={ids!r}")
        d027_reports: dict[str, dict[str, Any]] = {}
        for path in sorted((corpus_dir / "runs").glob("D027-*-manual-restoration.json")):
            report = _json(path)
            case_id = report.get("case_id")
            if case_id in d027_reports:
                raise AccountingError(f"duplicate D027 reports for {case_id}")
            d027_reports[case_id] = report
        cohort_ids = {item["case_id"] for item in cohort}
        unexpected = set(d027_reports) - cohort_ids
        if unexpected:
            raise AccountingError(f"D027 reports outside frozen cohort: {sorted(unexpected)}")
        rows_by_id = dict(zip(ids, screening))
        for case_id, report in d027_reports.items():
            if _case_identity(report) != _case_identity(rows_by_id[case_id]):
                raise AccountingError(f"{case_id}: D027 report has contradictory frozen identity")

        cases = []
        for case_id, row in zip(ids, screening):
            mutation = row["mutation"]
            report = None
            if mutation.get("report_path"):
                report = _json(_report_path(mutation["report_path"]))
                _validate_primary_report(case_id, row, report)
            primary_evaluated = mutation["status"] == "evaluated"
            primary_outcome = _lower(mutation.get("outcome"))
            d027_fields = _d027_fields(d027_reports.get(case_id))
            if primary_evaluated:
                source, evaluated = "primary", True
                outcome = primary_outcome
                semantic = _primary_semantic(row, report)
            elif d027_fields["d027_evaluated"]:
                source, evaluated = "D027", True
                outcome = d027_fields["d027_outcome"]
                semantic = d027_fields["d027_semantic_status"]
            else:
                source, evaluated, outcome, semantic = "none", False, None, "not-run"
            case = {
                "case_id": case_id, "batch": case_id[:3], "operator": row["operator"],
                "repository": row["repository"], "primary_status": row["screening"]["status"],
                "primary_evaluated": primary_evaluated, "primary_outcome": primary_outcome,
                "primary_semantic_status": _primary_semantic(row, report), **d027_fields,
                "combined_result_source": source, "combined_evaluated": evaluated,
                "combined_outcome": outcome, "combined_semantic_status": semantic,
            }
            cases.append(case)
        return cases
    finally:
        CORPUS_DIR, RUNS_DIR = old_corpus, old_runs


def _summarize(cases: Iterable[dict[str, Any]], layer: str) -> dict[str, int]:
    rows = list(cases)
    evaluated_key, outcome_key = f"{layer}_evaluated", f"{layer}_outcome"
    counts = Counter(row[outcome_key] for row in rows if row[evaluated_key])
    summary = {"selected": len(rows), "evaluated": sum(counts.values()),
               "non-evaluable": len(rows) - sum(counts.values())}
    for outcome in ("survived", "killed", "equivalent", "invalid", "timeout", "error"):
        summary[outcome] = counts[outcome]
    if layer == "primary":
        statuses = Counter(row["primary_status"] for row in rows)
        summary.update({status: statuses[status] for status in sorted(statuses)})
    return summary


def _d027_summary(cases: list[dict[str, Any]]) -> dict[str, int]:
    reports = [row for row in cases if row["d027_report_present"]]
    attempted = [row for row in reports if row["d027_assessment_status"] != "not-attempted"]
    return {
        "cohort": 24, "report_present": len(reports),
        "report_absent_not_attempted": 24 - len(reports),
        "substantive_restoration_attempted": len(attempted),
        "restoration_not_attempted": len(reports) - len(attempted),
        "restored": sum(row["d027_restored"] for row in reports),
        "not_restored": sum(row["d027_assessment_status"] == "not-restored" for row in reports),
        "mutation_evaluated": sum(row["d027_evaluated"] for row in reports),
    }


def _assert_expected(result: dict[str, Any]) -> None:
    for name, expected in EXPECTED.items():
        observed = result[name]
        bad = {key: (observed.get(key), value) for key, value in expected.items()
               if observed.get(key) != value}
        if bad:
            raise AccountingError(f"sanity check {name} disagrees with structured evidence: {bad}")
    for operator, expected in EXPECTED_OPERATORS.items():
        observed = result["b02_by_operator"][operator]
        bad = {key: (observed.get(key), value) for key, value in expected.items()
               if observed.get(key) != value}
        if bad:
            raise AccountingError(f"sanity check operator {operator} disagrees: {bad}")
    detection = result["confirmed_detection"]
    if (detection["killed"], detection["confirmed_non_equivalent_survived"],
            detection["denominator"]) != (2, 21, 23):
        raise AccountingError(f"confirmed detection sanity check disagrees: {detection}")


def calculate(corpus_dir: Path = CORPUS_DIR) -> dict[str, Any]:
    cases = build_case_table(corpus_dir)
    b01 = [row for row in cases if row["batch"] == "B01"]
    b02 = [row for row in cases if row["batch"] == "B02"]
    by_operator = {
        operator: _summarize((row for row in b02 if row["operator"] == operator), "combined")
        for operator in ("random-seed", "dependency-pin", "data-split", "cv-fold-count")
    }
    confirmed_survivors = sum(
        row["combined_outcome"] == "survived"
        and row["combined_semantic_status"] == "confirmed-non-equivalent"
        for row in cases
    )
    killed = sum(row["combined_outcome"] == "killed" for row in cases)
    denominator = killed + confirmed_survivors
    result = {
        "metadata": {"study": "MLReproMutate", "accounting_version": 1,
                     "intended_cases": 39, "b01_cases": 10, "b02_cases": 29},
        "totals": {"selected": 39, "b01": 10, "b02": 29},
        "primary": _summarize(cases, "primary"),
        "d027": _d027_summary(cases),
        "combined": _summarize(cases, "combined"),
        "b01": {"primary": _summarize(b01, "primary"),
                "combined": _summarize(b01, "combined")},
        "b02": {"primary": _summarize(b02, "primary"),
                "combined": _summarize(b02, "combined")},
        "b02_by_operator": by_operator,
        "confirmed_detection": {
            "killed": killed,
            "confirmed_non_equivalent_survived": confirmed_survivors,
            "denominator": denominator,
            "percentage": (100.0 * killed / denominator) if denominator else None,
        },
        "cases": cases,
    }
    # Convenience aliases make named sanity checks and API use unambiguous.
    result["b01_primary"], result["b01_combined"] = result["b01"]["primary"], result["b01"]["combined"]
    result["b02_primary"], result["b02_combined"] = result["b02"]["primary"], result["b02"]["combined"]
    _assert_expected(result)
    return result


def _ratio(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator} ({100.0 * numerator / denominator:.1f}%)" if denominator else "0/0 (n/a)"


def _line(summary: dict[str, int]) -> str:
    selected = summary["selected"]
    return (f"selected={selected}; evaluated={_ratio(summary['evaluated'], selected)}; "
            f"non-evaluable={_ratio(summary['non-evaluable'], selected)}; "
            f"SURVIVED={_ratio(summary['survived'], selected)}; "
            f"KILLED={_ratio(summary['killed'], selected)}; "
            f"EQUIVALENT={_ratio(summary['equivalent'], selected)}")


def print_summary(result: dict[str, Any], concise: bool = False) -> None:
    print("A. STUDY TOTALS")
    print("selected=39 (B01=10, B02=29)")
    print("B. PRIMARY RESULTS")
    print(f"full study: {_line(result['primary'])}")
    print(f"B02: {_line(result['b02']['primary'])}; "
          f"setup-failed={_ratio(result['b02']['primary']['setup-failed'], 29)}; "
          f"workflow-unavailable={_ratio(result['b02']['primary']['workflow-unavailable'], 29)}")
    print(f"B01: {_line(result['b01']['primary'])}; "
          f"setup-failed={_ratio(result['b01']['primary']['setup-failed'], 10)}")
    print("C. D027 RESTORATION")
    d = result["d027"]
    print(f"cohort={d['cohort']}; "
          f"report/assessment present={_ratio(d['report_present'], d['cohort'])}; "
          f"no report={_ratio(d['report_absent_not_attempted'], d['cohort'])}; "
          f"substantive restoration attempted={_ratio(d['substantive_restoration_attempted'], d['cohort'])}; "
          f"report-present not-attempted={_ratio(d['restoration_not_attempted'], d['cohort'])}; "
          f"restored={_ratio(d['restored'], d['cohort'])}; "
          f"not-restored={_ratio(d['not_restored'], d['cohort'])}; "
          f"mutation evaluated={_ratio(d['mutation_evaluated'], d['cohort'])}")
    print("D. COMBINED PRIMARY + D027")
    print(_line(result["combined"]))
    if concise:
        return
    print("E. B02 BY OPERATOR")
    for operator, summary in result["b02_by_operator"].items():
        print(f"{operator}: {_line(summary)}")
    print("F. B01 SUMMARY")
    print(f"primary: {_line(result['b01']['primary'])}")
    print(f"combined: {_line(result['b01']['combined'])}")
    print("G. STILL NON-EVALUABLE")
    remaining = [row["case_id"] for row in result["cases"] if not row["combined_evaluated"]]
    print(f"{len(remaining)}/39: {', '.join(remaining)}")
    print("H. D027 NOT ATTEMPTED")
    absent = [row["case_id"] for row in result["cases"]
              if row["primary_status"] == "setup-failed"
              and not row["d027_report_present"]]
    explicit = [row["case_id"] for row in result["cases"]
                if row["d027_assessment_status"] == "not-attempted"]
    print(f"no report={len(absent)}: {', '.join(absent)}")
    print(f"report present, restoration not-attempted={len(explicit)}: {', '.join(explicit)}")
    print("I. CONFIRMED-NON-EQUIVALENT DETECTION")
    detection = result["confirmed_detection"]
    print(f"KILLED / (KILLED + confirmed-non-equivalent SURVIVED) = "
          f"{detection['killed']}/{detection['denominator']} ({detection['percentage']:.1f}%)")


def write_csv(path: Path, cases: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CASE_FIELDS)
        writer.writeheader()
        writer.writerows({field: row[field] for field in CASE_FIELDS} for row in cases)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--csv", type=Path, metavar="PATH", help="write the 39-row case table")
    args = parser.parse_args(argv)
    result = calculate()
    if args.csv:
        write_csv(args.csv, result["cases"])
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_summary(result, concise=bool(args.csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
