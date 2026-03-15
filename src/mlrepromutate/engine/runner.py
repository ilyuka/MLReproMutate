import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a command inside a project workspace."""

    command: tuple[str, ...]
    return_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


class ExperimentRunner:
    """Execute experiment or validation commands in a project workspace."""

    def __init__(
        self,
        command: Sequence[str],
        timeout_seconds: float = 300.0,
    ) -> None:
        if not command:
            raise ValueError("Command must not be empty.")

        if timeout_seconds <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self.command = tuple(command)
        self.timeout_seconds = timeout_seconds

    def run(self, project_root: Path) -> ExecutionResult:
        """Execute the configured command in the given project directory."""

        project_root = project_root.resolve()

        if not project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {project_root}"
            )

        if not project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {project_root}"
            )

        start_time = time.monotonic()

        try:
            completed = subprocess.run(
                self.command,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start_time

            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")

            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")

            return ExecutionResult(
                command=self.command,
                return_code=None,
                stdout=stdout,
                stderr=stderr,
                duration_seconds=duration,
                timed_out=True,
            )

        duration = time.monotonic() - start_time

        return ExecutionResult(
            command=self.command,
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_seconds=duration,
            timed_out=False,
        )