import json
from pathlib import Path

from mlrepromutate.engine.runner import ExecutionResult
from mlrepromutate.models import (
    MutationCandidate,
    MutationOutcome,
    MutationResult,
)
from mlrepromutate.operators.dependency import (
    RelaxRequirementsPinOperator,
)
from mlrepromutate.reporting import (
    build_run_report,
    write_run_report,
)


def test_build_run_report_contains_provenance(
    tmp_path: Path,
) -> None:
    candidate = MutationCandidate(
        operator="relax_requirements_pin",
        category="dependency",
        target=Path("requirements.txt"),
        description="Relax numpy dependency pin.",
        metadata={
            "package": "numpy",
            "version": "2.1.0",
            "line_number": 1,
        },
    )

    mutation_result = MutationResult(
        candidate=candidate,
        outcome=MutationOutcome.SURVIVED,
        duration_seconds=1.5,
        reason="Safeguards did not detect the mutation.",
        metadata={
            "return_code": 0,
            "stdout": "ok\n",
            "stderr": "",
        },
    )

    baseline = ExecutionResult(
        command=("python", "validate.py"),
        return_code=0,
        stdout="baseline ok\n",
        stderr="",
        duration_seconds=2.0,
        timed_out=False,
    )

    operator = RelaxRequirementsPinOperator(
        requirements_file=Path("requirements.txt"),
    )

    report = build_run_report(
        project_root=tmp_path,
        validation_command="python validate.py",
        timeout_seconds=300.0,
        operator=operator,
        baseline=baseline,
        results=[mutation_result],
        requirements_file=Path("requirements.txt"),
        dependency_mode="manifest",
    )

    assert report["schema_version"] == 1
    assert report["summary"]["candidates"] == 1
    assert report["summary"]["outcomes"]["survived"] == 1
    assert report["operator"]["dependency_mode"] == "manifest"

    mutation = report["mutations"][0]

    assert mutation["target"] == "requirements.txt"
    assert mutation["candidate_metadata"]["package"] == "numpy"
    assert mutation["outcome"] == "survived"
    assert mutation["result_metadata"]["return_code"] == 0

def test_write_run_report_writes_json(
    tmp_path: Path,
) -> None:
    output = tmp_path / "reports" / "run.json"

    report = {
        "schema_version": 1,
        "summary": {
            "candidates": 0,
        },
    }

    write_run_report(output, report)

    loaded = json.loads(
        output.read_text(encoding="utf-8")
    )

    assert loaded == report

