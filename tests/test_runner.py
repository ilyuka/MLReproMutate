import subprocess
import sys
from pathlib import Path

import pytest

from mlrepromutate.engine import ExperimentRunner


def test_runner_executes_successful_command(tmp_path: Path) -> None:
    runner = ExperimentRunner(
        [
            sys.executable,
            "-c",
            "print('experiment completed')",
        ]
    )

    result = runner.run(tmp_path)

    assert result.return_code == 0
    assert result.stdout.strip() == "experiment completed"
    assert result.stderr == ""
    assert result.timed_out is False
    assert result.duration_seconds >= 0


def test_runner_captures_failed_command(tmp_path: Path) -> None:
    runner = ExperimentRunner(
        [
            sys.executable,
            "-c",
            "import sys; print('failure', file=sys.stderr); sys.exit(3)",
        ]
    )

    result = runner.run(tmp_path)

    assert result.return_code == 3
    assert "failure" in result.stderr
    assert result.timed_out is False


def test_runner_executes_inside_project_directory(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    runner = ExperimentRunner(
        [
            sys.executable,
            "-c",
            "import pathlib; print(pathlib.Path.cwd())",
        ]
    )

    result = runner.run(project)

    assert result.return_code == 0
    assert Path(result.stdout.strip()) == project.resolve()


def test_runner_handles_timeout(tmp_path: Path) -> None:
    runner = ExperimentRunner(
        [
            sys.executable,
            "-c",
            "import time; time.sleep(1)",
        ],
        timeout_seconds=0.05,
    )

    result = runner.run(tmp_path)

    assert result.return_code is None
    assert result.timed_out is True
    assert result.duration_seconds >= 0


def test_runner_rejects_empty_command() -> None:
    with pytest.raises(ValueError, match="Command must not be empty"):
        ExperimentRunner([])


def test_runner_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="Timeout must be greater than zero"):
        ExperimentRunner(
            [sys.executable, "-c", "pass"],
            timeout_seconds=0,
        )


def test_runner_rejects_missing_project(tmp_path: Path) -> None:
    runner = ExperimentRunner([sys.executable, "-c", "pass"])

    with pytest.raises(FileNotFoundError):
        runner.run(tmp_path / "missing")


def test_runner_rejects_file_as_project(tmp_path: Path) -> None:
    project_file = tmp_path / "project.txt"
    project_file.write_text("not a directory", encoding="utf-8")

    runner = ExperimentRunner([sys.executable, "-c", "pass"])

    with pytest.raises(NotADirectoryError):
        runner.run(project_file)

def test_with_python_executable_replaces_python_command() -> None:
    runner = ExperimentRunner(
        [
            "/some/environment/bin/python",
            "validate.py",
            "--flag",
        ],
        timeout_seconds=42,
    )

    replaced = runner.with_python_executable(
        Path("/another/environment/bin/python")
    )

    assert replaced.command == (
        "/another/environment/bin/python",
        "validate.py",
        "--flag",
    )
    assert replaced.timeout_seconds == 42

def test_with_python_executable_rejects_non_python_command() -> None:
    runner = ExperimentRunner(
        ["pytest", "-q"],
    )

    with pytest.raises(
        ValueError,
        match="requires a Python validation command",
    ):
        runner.with_python_executable(
            Path("/tmp/env/bin/python")
        )

def test_runner_disables_stdin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(
        command: tuple[str, ...],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        captured["stdin"] = kwargs.get("stdin")
        return subprocess.CompletedProcess(
            command,
            returncode=0,
            stdout="",
            stderr="",
        )

    monkeypatch.setattr(
        "mlrepromutate.engine.runner.subprocess.run",
        fake_run,
    )

    runner = ExperimentRunner(
        [sys.executable, "-c", "pass"],
    )

    result = runner.run(tmp_path)

    assert result.return_code == 0
    assert captured["stdin"] is subprocess.DEVNULL

def test_runner_does_not_wait_for_interactive_input(
    tmp_path: Path,
) -> None:
    runner = ExperimentRunner(
        [
            sys.executable,
            "-c",
            "input('Enter value: ')",
        ],
        timeout_seconds=2,
    )

    result = runner.run(tmp_path)

    assert result.timed_out is False
    assert result.return_code != 0
    assert "EOFError" in result.stderr

