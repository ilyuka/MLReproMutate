import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "benchmarks" / "corpus" / "b02_harness.py"
FRAME_PATH = ROOT / "benchmarks" / "corpus" / "sampling_frame.jsonl"
sys.path.insert(0, str(HARNESS_PATH.parent))

SPEC = importlib.util.spec_from_file_location("b02_harness", HARNESS_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

load_sampling_frame = MODULE.load_sampling_frame
next_unprocessed_case = MODULE.next_unprocessed_case
processed_case_ids = MODULE.processed_case_ids
case_work_dir = MODULE.case_work_dir
run_candidate_command = MODULE.run_candidate_command
timeout_for_class = MODULE.timeout_for_class
d025_recoverable_cases = MODULE.d025_recoverable_cases
replace_ledger_case = MODULE.replace_ledger_case
validate_d025_report = MODULE.validate_d025_report


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def small_frame() -> list[dict]:
    return [
        {
            "case_id": f"B02-{index:02d}",
            "repository": f"owner/repository-{index}",
            "revision": str(index) * 40,
            "operator": "random-seed",
        }
        for index in range(1, 4)
    ]


@pytest.fixture
def candidate_work_dir() -> Path:
    work_root = Path("/home/ilya/.cache/mlrepromutate/b02")
    try:
        path = Path(tempfile.mkdtemp(prefix="synthetic-harness-test-", dir=work_root))
    except OSError as exc:
        pytest.skip(f"B02 synthetic work root is not writable: {exc}")
    try:
        yield path
    finally:
        shutil.rmtree(path)


def test_loads_all_frozen_cases_in_case_id_order() -> None:
    frame = load_sampling_frame(FRAME_PATH)

    assert len(frame) == 29
    assert [record["case_id"] for record in frame] == [
        f"B02-{index:02d}" for index in range(1, 30)
    ]


def test_detects_processed_cases_from_ledger_identity_and_report(
    tmp_path: Path,
) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    runs = tmp_path / "runs"
    runs.mkdir()
    legacy_record = dict(frame[0])
    legacy_record.pop("case_id")
    write_jsonl(ledger, [legacy_record, frame[1]])
    (runs / "B02-03-result.json").write_text("{}\n", encoding="utf-8")
    (runs / "B02-01-amended-policy-rerun.json").write_text("{}\n", encoding="utf-8")

    assert processed_case_ids(frame, ledger, runs) == {
        "B02-01",
        "B02-02",
        "B02-03",
    }


def test_b02_01_remains_pending_until_distinct_amended_rerun_report(
    tmp_path: Path,
) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    runs = tmp_path / "runs"
    runs.mkdir()
    write_jsonl(ledger, [frame[0], frame[1]])
    (runs / "B02-01-original.json").write_text("{}\n", encoding="utf-8")

    assert processed_case_ids(frame, ledger, runs) == {"B02-02"}
    assert next_unprocessed_case(frame, {"B02-02"}) == frame[0]


def test_d025_timeout_policy_has_explicit_stage_classes() -> None:
    assert timeout_for_class("setup-install") == 1800.0
    assert timeout_for_class("clone-checkout-venv") == 300.0
    assert timeout_for_class("baseline-validation") == 900.0
    assert timeout_for_class("mutant-validation") == 900.0
    assert timeout_for_class("semantic-verification") == 300.0
    assert MODULE.D025_MAX_CORRECTIONS == 3

    with pytest.raises(ValueError, match="unknown B02 timeout class"):
        timeout_for_class("setup")


def test_chooses_first_unprocessed_case() -> None:
    frame = small_frame()

    assert next_unprocessed_case(frame, {"B02-01"}) == frame[1]


def test_returns_none_when_all_cases_are_processed() -> None:
    frame = small_frame()

    assert (
        next_unprocessed_case(
            frame,
            {record["case_id"] for record in frame},
        )
        is None
    )


def test_current_normal_next_case_remains_b02_21() -> None:
    frame = load_sampling_frame(FRAME_PATH)
    assert (
        next_unprocessed_case(frame, processed_case_ids(frame))["case_id"] == "B02-21"
    )


def test_recoverable_cases_are_setup_failures_in_frame_order_and_ignore_s1(
    tmp_path: Path,
) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    runs = tmp_path / "runs"
    runs.mkdir()
    records = []
    for case, status in zip(
        frame, ("setup-failed", "eligible", "workflow-unavailable"), strict=True
    ):
        records.append({**case, "screening": {"status": status}})
    write_jsonl(ledger, records)
    (runs / "B02-01-S1-sensitivity.json").write_text("{}\n", encoding="utf-8")

    assert [
        case["case_id"] for case in d025_recoverable_cases(frame, ledger, runs)
    ] == ["B02-01"]
    (runs / "B02-01-D025-recovery.json").write_text("{}\n", encoding="utf-8")
    assert d025_recoverable_cases(frame, ledger, runs) == []


def test_recovery_replaces_one_ledger_record_without_touching_prior_record() -> None:
    records = [{"case_id": "B02-01", "value": "old"}, {"case_id": "B02-02"}]
    original = json.loads(json.dumps(records))
    updated = replace_ledger_case(
        records, "B02-01", {"case_id": "B02-01", "value": "new"}
    )
    assert updated == [{"case_id": "B02-01", "value": "new"}, {"case_id": "B02-02"}]
    assert records == original


def d025_report(case: dict, *, symmetric: bool = True) -> dict:
    return {
        "d025_policy": "D025",
        "execution_mode": "recovery",
        "infrastructure_valid": True,
        "frozen_case": {
            "case_id": case["case_id"],
            "repository": case["repository"],
            "revision": case["revision"],
            "operator": case["operator"],
            "candidate_index": case.get("candidate_index"),
            "workflow": case.get("workflow_command"),
            "oracle_kind": case.get("oracle_kind"),
        },
        "compatibility_corrections": [
            {
                "class": "missing-runtime-test-validation-dependency",
                "description": "install missing dependency",
                "reason": "workflow needs it",
                "prior_failure": "ModuleNotFoundError",
            }
        ],
        "corrections_used": 1,
        "timeout_policy_seconds": MODULE.TIMEOUT_SECONDS_BY_CLASS,
        "prior_report_path": "benchmarks/corpus/runs/B02-01-old.json",
        "environments": {"baseline": "/work/base", "mutant": "/work/mutant"},
        "mutation_evaluated": True,
        "correction_symmetry": symmetric,
    }


def test_d025_evaluated_report_requires_correction_symmetry() -> None:
    case = {
        **small_frame()[0],
        "candidate_index": None,
        "workflow_command": None,
        "oracle_kind": None,
    }
    validate_d025_report(d025_report(case), case, recovery=True)
    with pytest.raises(ValueError, match="symmetry"):
        validate_d025_report(d025_report(case, symmetric=False), case, recovery=True)


def test_existing_pre_d025_report_remains_parseable() -> None:
    path = ROOT / "benchmarks/corpus/runs/B02-04-torchdiffeq-seed.json"
    assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


@pytest.mark.parametrize(
    "case_ids",
    [
        ["B02-01", "B02-01"],
        ["B02-01", "B2-02"],
        ["B02-02", "B02-01"],
    ],
)
def test_rejects_duplicate_malformed_or_out_of_order_frame_ids(
    tmp_path: Path,
    case_ids: list[str],
) -> None:
    records = small_frame()[:2]
    for record, case_id in zip(records, case_ids, strict=True):
        record["case_id"] = case_id
    frame_path = tmp_path / "sampling_frame.jsonl"
    write_jsonl(frame_path, records)

    with pytest.raises(ValueError):
        load_sampling_frame(frame_path)


def test_rejects_duplicate_processed_case_in_ledger(tmp_path: Path) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    write_jsonl(ledger, [frame[0], frame[0]])

    with pytest.raises(ValueError, match="duplicate B02 case"):
        processed_case_ids(frame, ledger, tmp_path / "missing-runs")


def test_rejects_malformed_case_id_in_ledger(tmp_path: Path) -> None:
    frame = small_frame()
    ledger = tmp_path / "screening.jsonl"
    write_jsonl(ledger, [{**frame[0], "case_id": None}])

    with pytest.raises(ValueError, match="malformed B02 case_id"):
        processed_case_ids(frame, ledger, tmp_path / "missing-runs")


def test_local_command_writes_full_logs_and_compact_success_summary(
    candidate_work_dir: Path,
) -> None:
    command = [
        "/usr/bin/python3",
        "-c",
        "import sys; print('hello'); print('warning', file=sys.stderr)",
    ]

    result = run_candidate_command(
        "B02-01",
        "baseline",
        command,
        candidate_work_dir,
        2,
        candidate_work_dir,
    )

    assert result["command"] == command
    assert result["return_code"] == 0
    assert result["timed_out"] is False
    assert result["duration_seconds"] >= 0
    assert Path(result["stdout_log"]).read_text(encoding="utf-8") == "hello\n"
    assert Path(result["stderr_log"]).read_text(encoding="utf-8") == "warning\n"
    assert result["stdout_tail"] == ["hello"]
    summary_path = (
        candidate_work_dir / "B02-01" / "stages" / "baseline" / "summary.json"
    )
    assert json.loads(summary_path.read_text(encoding="utf-8")) == result


def test_local_command_records_nonzero_return_code(candidate_work_dir: Path) -> None:
    command = ["/usr/bin/python3", "-c", "import sys; sys.exit(7)"]

    result = run_candidate_command(
        "B02-01", "setup", command, candidate_work_dir, 2, candidate_work_dir
    )

    assert result["return_code"] == 7
    assert result["timed_out"] is False


def test_local_command_records_short_timeout(candidate_work_dir: Path) -> None:
    command = ["/usr/bin/python3", "-c", "import time; time.sleep(1)"]

    result = run_candidate_command(
        "B02-01",
        "timeout-check",
        command,
        candidate_work_dir,
        0.02,
        candidate_work_dir,
    )

    assert result["return_code"] is None
    assert result["timed_out"] is True
    assert Path(result["stdout_log"]).exists()
    assert Path(result["stderr_log"]).exists()


def test_compact_tails_are_line_bounded_but_full_log_is_retained(
    candidate_work_dir: Path,
) -> None:
    command = [
        "/usr/bin/python3",
        "-c",
        "print('\\n'.join(f'line-{i}' for i in range(100)))",
    ]

    result = run_candidate_command(
        "B02-01",
        "bounded",
        command,
        candidate_work_dir,
        2,
        candidate_work_dir,
        tail_lines=4,
    )

    assert result["stdout_tail"] == ["line-96", "line-97", "line-98", "line-99"]
    assert result["stdout_tail_truncated"] is True
    assert (
        len(Path(result["stdout_log"]).read_text(encoding="utf-8").splitlines()) == 100
    )


def test_case_work_dir_is_deterministic_and_configurable(
    tmp_path: Path,
) -> None:
    configured = tmp_path / "persistent-work"

    assert case_work_dir("B02-01", configured) == configured / "B02-01"
    assert case_work_dir("B02-01") == case_work_dir("B02-01")
