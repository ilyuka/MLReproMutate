import json
import re
from pathlib import Path

from typer.testing import CliRunner

import mlrepromutate
from mlrepromutate.cli import app

ANSI_ESCAPE = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"
)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == mlrepromutate.__version__


def test_run_reports_survived_mutation(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0
    assert "SURVIVED" in result.stdout
    assert "1 mutations" in result.stdout
    assert "0 killed" in result.stdout
    assert "1 survived" in result.stdout

    assert "Detected 1 mutation candidates." in result.stdout
    assert "Validating baseline..." in result.stdout
    assert "Baseline validation passed in " in result.stdout
    assert "[1/1]" in result.stdout
    assert "SURVIVED" in result.stdout


def test_run_reports_no_applicable_mutations(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy>=2.1.0\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python -c \"raise SystemExit(0)\"",
        ],
    )

    assert result.exit_code == 0
    assert "No applicable mutations found." in result.stdout


def test_run_reports_baseline_failure(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(1)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 2
    assert "Baseline error" in result.output

def test_run_can_scope_dependency_mutations_to_one_file(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "requirements-optional.txt").write_text(
        "torch==2.8.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python validate.py",
            "--requirements-file",
            "requirements.txt",
        ],
    )

    assert result.exit_code == 0
    assert "Detected 1 mutation candidates." in result.stdout
    assert "requirements.txt:1" in result.stdout
    assert "numpy" in result.stdout
    assert "torch" not in result.stdout

def test_run_can_write_json_report(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "run.json"

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python validate.py",
            "--requirements-file",
            "requirements.txt",
            "--json-out",
            str(report_path),
        ],
    )

    assert result.exit_code == 0
    assert report_path.exists()

    report = json.loads(
        report_path.read_text(encoding="utf-8")
    )

    assert report["schema_version"] == 2
    assert report["summary"]["candidates"] == 1
    assert report["summary"]["outcomes"]["survived"] == 1

def test_resolved_mode_requires_requirements_file(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "python validate.py",
            "--dependency-mode",
            "resolved",
        ],
    )

    assert result.exit_code != 0
    output = strip_ansi(result.output)

    assert "requires" in output
    assert "requirements-file" in output

def test_resolved_mode_requires_python_command(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--command",
            "pytest -q",
            "--requirements-file",
            "requirements.txt",
            "--dependency-mode",
            "resolved",
        ],
    )

    assert result.exit_code != 0
    assert "requires a Python" in result.output
    assert "validation command" in result.output

def test_run_can_use_random_seed_operator(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "import random\n"
        "\n"
        "def run():\n"
        "    random.seed(42)\n"
        "    return random.random()\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "from experiment import run\n"
        "\n"
        "value = run()\n"
        "assert 0.0 <= value < 1.0\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "random-seed",
            "--python-file",
            "experiment.py",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0
    assert "Detected 1 mutation candidates." in result.stdout
    assert "experiment.py:4" in result.stdout
    assert "SURVIVED" in result.stdout


def test_random_seed_operator_can_write_json_report(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "import random\n"
        "random.seed(42)\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    report_path = tmp_path / "seed-run.json"

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "random-seed",
            "--python-file",
            "experiment.py",
            "--command",
            "python validate.py",
            "--json-out",
            str(report_path),
        ],
    )

    assert result.exit_code == 0

    report = json.loads(
        report_path.read_text(encoding="utf-8")
    )

    assert report["schema_version"] == 2
    assert report["operator"]["category"] == "randomness"
    assert (
        report["operator"]["name"]
        == "change_python_random_seed"
    )
    assert report["operator"]["configuration"] == {
        "python_file": "experiment.py",
    }

    mutation = report["mutations"][0]

    assert mutation["candidate_metadata"]["original_seed"] == 42
    assert mutation["candidate_metadata"]["mutated_seed"] == 43
    assert mutation["outcome"] == "survived"


def test_random_seed_rejects_dependency_options(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "random-seed",
            "--command",
            "python validate.py",
            "--dependency-mode",
            "resolved",
        ],
    )

    assert result.exit_code != 0

    output = strip_ansi(result.output)

    assert "dependency-mode" in output
    assert "dependency-pin" in result.output


def test_run_can_use_data_split_operator(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "from sklearn.model_selection import train_test_split\n"
        "train_test_split(X, y, stratify=y)\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "data-split",
            "--python-file",
            "experiment.py",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0
    assert "Detected 1 mutation candidates." in result.stdout
    assert "experiment.py:2" in result.stdout
    assert "SURVIVED" in result.stdout


def test_run_can_use_cv_fold_count_operator(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        "cv = StratifiedKFold(n_splits=5)\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "cv-fold-count",
            "--python-file",
            "experiment.py",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0
    assert "Detected 1 mutation candidates." in result.stdout
    assert "experiment.py:2" in result.stdout
    assert "SURVIVED" in result.stdout



def test_run_can_select_one_mutation_candidate(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        "first = StratifiedKFold(n_splits=5)\n"
        "second = StratifiedKFold(n_splits=10)\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "cv-fold-count",
            "--python-file",
            "experiment.py",
            "--candidate-index",
            "1",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0
    assert "Detected 2 mutation candidates." in result.stdout
    assert "Selected mutation candidate 1 of 2." in result.stdout
    assert "Summary: 1 mutations" in result.stdout


def test_run_rejects_in_place_resolved_dependency_mode(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "requirements.txt").write_text(
        "demo==1.0.0\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "dependency-pin",
            "--requirements-file",
            "requirements.txt",
            "--dependency-mode",
            "resolved",
            "--execution-mode",
            "in-place",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 2

    normalized_output = " ".join(result.output.split())

    assert "execution-mode" in normalized_output
    assert "in-place" in normalized_output
    assert "dependency-mode" in normalized_output
    assert "resolved" in normalized_output


def test_run_supports_repeated_sandbox_excludes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "import random\n"
        "random.seed(42)\n",
        encoding="utf-8",
    )

    data = project / "data"
    data.mkdir()
    (data / "large.bin").write_bytes(b"large")

    checkpoints = project / "checkpoints"
    checkpoints.mkdir()
    (checkpoints / "model.bin").write_bytes(b"model")

    (project / "validate.py").write_text(
        "from pathlib import Path\n"
        "raise SystemExit(\n"
        "    0 if not Path('data').exists() "
        "and not Path('checkpoints').exists() else 1\n"
        ")\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "random-seed",
            "--python-file",
            "experiment.py",
            "--execution-mode",
            "sandbox",
            "--exclude",
            "data",
            "--exclude",
            "checkpoints",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 0


def test_run_rejects_exclude_with_in_place_mode(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    (project / "experiment.py").write_text(
        "import random\n"
        "random.seed(42)\n",
        encoding="utf-8",
    )

    (project / "validate.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(project),
            "--operator",
            "random-seed",
            "--python-file",
            "experiment.py",
            "--execution-mode",
            "in-place",
            "--exclude",
            "data",
            "--command",
            "python validate.py",
        ],
    )

    assert result.exit_code == 2

    output = " ".join(result.output.split())

    assert "exclude" in output
    assert "execution-mode" in output
    assert "sandbox" in output
