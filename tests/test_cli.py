from pathlib import Path

from typer.testing import CliRunner

from mlrepromutate.cli import app


runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.0.0" in result.stdout


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