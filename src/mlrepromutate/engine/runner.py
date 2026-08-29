import os
import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


class CommandResolutionError(ValueError):
    """A requested ``python`` or ``python3`` executable was not found."""


def resolve_command_executable(
    command: Sequence[str],
) -> tuple[str, ...]:
    """Resolve portable Python command aliases without changing other commands."""

    resolved = tuple(command)

    if not resolved:
        raise ValueError("Command must not be empty.")

    requested = resolved[0]

    if requested not in {"python", "python3"}:
        return resolved

    executable = shutil.which(requested)

    if executable is None:
        fallback = "python3" if requested == "python" else "python"
        executable = shutil.which(fallback)

    if executable is None:
        raise CommandResolutionError(
            "Could not find either 'python' or 'python3' on PATH."
        )

    return (
        executable,
        *resolved[1:],
    )


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a command inside a project workspace.

    Attributes:
        command: Resolved command passed to the subprocess.
        return_code: Process exit status, or ``None`` after a timeout.
        stdout: Captured standard output.
        stderr: Captured standard error.
        duration_seconds: Elapsed execution time in seconds.
        timed_out: Whether execution exceeded the configured timeout.
    """

    command: tuple[str, ...]
    return_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


class ExperimentRunner:
    """Execute an experiment or validation command in a project workspace.

    Args:
        command: Command and arguments to execute.
        timeout_seconds: Maximum execution time in seconds.

    Attributes:
        command: Resolved command and arguments.
        timeout_seconds: Maximum execution time in seconds.

    Raises:
        ValueError: ``command`` is empty or ``timeout_seconds`` is not
            positive.
        CommandResolutionError: A requested Python executable is unavailable.
    """

    def __init__(
        self,
        command: Sequence[str],
        timeout_seconds: float = 300.0,
    ) -> None:
        if not command:
            raise ValueError("Command must not be empty.")

        if timeout_seconds <= 0:
            raise ValueError("Timeout must be greater than zero.")

        self.command = resolve_command_executable(command)
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        project_root: Path,
        *,
        prefer_project_sources: bool = False,
    ) -> ExecutionResult:
        """Execute the configured command in the given project directory.

        Args:
            project_root: Directory in which to execute the command.
            prefer_project_sources: Prepend the workspace and its ``src``
                directory to ``PYTHONPATH`` when true.

        Returns:
            Captured command result, including timeout status.

        Raises:
            FileNotFoundError: ``project_root`` does not exist.
            NotADirectoryError: ``project_root`` is not a directory.
        """

        project_root = project_root.resolve()

        if not project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {project_root}"
            )

        if not project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {project_root}"
            )

        environment: dict[str, str] | None = None

        if prefer_project_sources:
            environment = os.environ.copy()
            python_paths: list[str] = []

            src_path = project_root / "src"
            if src_path.is_dir():
                python_paths.append(str(src_path))

            python_paths.append(str(project_root))

            inherited_python_path = environment.get("PYTHONPATH")
            if inherited_python_path:
                python_paths.append(inherited_python_path)

            environment["PYTHONPATH"] = os.pathsep.join(python_paths)

        start_time = time.monotonic()

        try:
            completed = subprocess.run(
                self.command,
                cwd=project_root,
                env=environment,
                stdin=subprocess.DEVNULL,
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
    
    def with_python_executable(
        self,
        python_executable: Path,
    ) -> "ExperimentRunner":
        """Return a runner using another Python executable.

        Args:
            python_executable: Python executable for the returned runner.

        Returns:
            A new runner with the executable replaced.

        Raises:
            ValueError: The configured command is not a Python command.
        """

        executable_name = Path(self.command[0]).name

        if not executable_name.startswith("python"):
            raise ValueError(
                "Resolved dependency mode currently requires "
                "a Python validation command."
            )

        return ExperimentRunner(
            (
                str(python_executable),
                *self.command[1:],
            ),
            timeout_seconds=self.timeout_seconds,
        )
