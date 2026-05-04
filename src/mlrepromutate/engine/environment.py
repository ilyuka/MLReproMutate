import json
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvironmentResolutionResult:
    """Result of constructing a resolved Python environment."""

    python_executable: Path | None
    return_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool


class VirtualEnvironmentResolver:
    """Create an isolated venv and install a requirements manifest."""

    def __init__(
        self,
        bootstrap_python: Path,
        timeout_seconds: float = 600.0,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError(
                "Environment resolution timeout must be positive."
            )

        self.bootstrap_python = bootstrap_python
        self.timeout_seconds = timeout_seconds

    def resolve(
        self,
        project_root: Path,
        requirements_file: Path,
    ) -> EnvironmentResolutionResult:
        """Create a fresh venv and install the selected requirements file."""

        environment_root = project_root / ".mlrepromutate-env"
        environment_python = environment_root / "bin" / "python"
        requirements_path = project_root / requirements_file

        started = time.monotonic()

        try:
            create_result = subprocess.run(
                [
                    str(self.bootstrap_python),
                    "-m",
                    "venv",
                    str(environment_root),
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return EnvironmentResolutionResult(
                python_executable=None,
                return_code=None,
                stdout=_decode_timeout_output(exc.stdout),
                stderr=_decode_timeout_output(exc.stderr),
                duration_seconds=time.monotonic() - started,
                timed_out=True,
            )

        if create_result.returncode != 0:
            return EnvironmentResolutionResult(
                python_executable=None,
                return_code=create_result.returncode,
                stdout=create_result.stdout,
                stderr=create_result.stderr,
                duration_seconds=time.monotonic() - started,
                timed_out=False,
            )

        elapsed = time.monotonic() - started
        remaining = self.timeout_seconds - elapsed

        if remaining <= 0:
            return EnvironmentResolutionResult(
                python_executable=environment_python,
                return_code=None,
                stdout=create_result.stdout,
                stderr=create_result.stderr,
                duration_seconds=elapsed,
                timed_out=True,
            )

        try:
            install_result = subprocess.run(
                [
                    str(environment_python),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_path),
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return EnvironmentResolutionResult(
                python_executable=environment_python,
                return_code=None,
                stdout=(
                    create_result.stdout
                    + _decode_timeout_output(exc.stdout)
                ),
                stderr=(
                    create_result.stderr
                    + _decode_timeout_output(exc.stderr)
                ),
                duration_seconds=time.monotonic() - started,
                timed_out=True,
            )

        return EnvironmentResolutionResult(
            python_executable=environment_python,
            return_code=install_result.returncode,
            stdout=create_result.stdout + install_result.stdout,
            stderr=create_result.stderr + install_result.stderr,
            duration_seconds=time.monotonic() - started,
            timed_out=False,
        )

    def distribution_version(
        self,
        python_executable: Path,
        distribution: str,
    ) -> str | None:
        """Return an installed distribution version."""

        result = subprocess.run(
            [
                str(python_executable),
                "-c",
                (
                    "import importlib.metadata; "
                    f"print(importlib.metadata.version({distribution!r}))"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            return None

        resolved = result.stdout.strip()

        return resolved or None

    def distribution_versions(
        self,
        python_executable: Path,
    ) -> dict[str, str]:
        """Return installed distribution names and versions."""

        script = (
            "import importlib.metadata as metadata, json; "
            "print(json.dumps({"
            "d.metadata['Name']: d.version "
            "for d in metadata.distributions() "
            "if d.metadata.get('Name')"
            "}))"
        )

        result = subprocess.run(
            [
                str(python_executable),
                "-c",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            return {}

        raw_versions = json.loads(result.stdout)

        return {
            normalize_distribution_name(name): package_version
            for name, package_version in raw_versions.items()
        }


def _decode_timeout_output(
    value: str | bytes | None,
) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode(
            errors="replace",
        )

    return value


def normalize_distribution_name(name: str) -> str:
    """Normalize a Python distribution name."""

    return re.sub(
        r"[-_.]+",
        "-",
        name,
    ).lower()