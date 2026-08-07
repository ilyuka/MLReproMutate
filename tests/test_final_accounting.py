import csv
import json
from pathlib import Path

from benchmarks.corpus import final_accounting as accounting


def result():
    return accounting.calculate()


def cases_by_id():
    return {row["case_id"]: row for row in result()["cases"]}


def test_exact_intended_case_set_without_duplicates():
    cases = result()["cases"]
    ids = [row["case_id"] for row in cases]
    assert len(cases) == len(set(ids)) == 39
    assert ids == list(accounting.EXPECTED_IDS)


def test_canonical_primary_corrections_and_sensitivity_exclusion():
    cases = cases_by_id()
    assert cases["B02-01"]["primary_outcome"] == "survived"
    assert cases["B02-01"]["primary_status"] == "eligible"
    assert cases["B02-20"]["primary_status"] == "setup-failed"
    assert cases["B02-20"]["primary_evaluated"] is False
    screening = accounting._jsonl(accounting.CORPUS_DIR / "screening.jsonl")
    assert screening[29]["mutation"]["report_path"].endswith("B02-20-corrective-primary-rerun.json")
    assert cases["B02-25"]["primary_status"] == "workflow-unavailable"
    assert cases["B02-25"]["primary_semantic_status"] == "not-run"
    corrective = accounting._json(accounting.CORPUS_DIR / "runs/B02-25-classification-corrective.json")
    assert corrective["classification_correction"]["target_execution_status"] == "not-exercised"
    # B02-03 has an S1 report, but its canonical primary remains non-evaluated.
    assert cases["B02-03"]["primary_status"] == "setup-failed"
    assert cases["B02-03"]["primary_evaluated"] is False


def test_combined_layering_examples():
    cases = cases_by_id()
    assert cases["B02-01"]["combined_result_source"] == "primary"
    assert cases["B01-02"]["primary_evaluated"] is False
    assert cases["B01-02"]["combined_result_source"] == "D027"
    assert cases["B01-02"]["combined_outcome"] == "survived"
    assert cases["B01-07"]["d027_report_present"] is True
    assert cases["B01-07"]["d027_assessment_status"] == "not-attempted"
    assert cases["B01-07"]["d027_restored"] is False
    assert cases["B02-15"]["combined_outcome"] == "killed"
    for case_id in ("B02-27", "B02-28", "B02-29"):
        assert cases[case_id]["combined_result_source"] == "D027"
        assert cases[case_id]["combined_outcome"] == "survived"


def test_expected_primary_and_combined_totals():
    value = result()
    for name, expected in accounting.EXPECTED.items():
        observed = value[name]
        assert {key: observed[key] for key in expected} == expected


def test_expected_b02_operator_totals():
    observed = result()["b02_by_operator"]
    for operator, expected in accounting.EXPECTED_OPERATORS.items():
        assert {key: observed[operator][key] for key in expected} == expected


def test_confirmed_detection():
    detection = result()["confirmed_detection"]
    assert detection["killed"] == 2
    assert detection["confirmed_non_equivalent_survived"] == 21
    assert detection["denominator"] == 23
    assert round(detection["percentage"], 1) == 8.7


def test_json_serialization():
    encoded = json.dumps(result(), sort_keys=True)
    assert json.loads(encoded)["metadata"]["intended_cases"] == 39


def test_csv_header_and_39_rows(tmp_path: Path):
    path = tmp_path / "cases.csv"
    accounting.write_csv(path, result()["cases"])
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(accounting.CASE_FIELDS)
    assert len(rows) == 40
