import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path
from types import TracebackType


def normalize_sandbox_excludes(
    excludes: Sequence[Path],
) -> tuple[Path, ...]:
    """Validate and normalize project-relative sandbox exclusions."""

    normalized: list[Path] = []

    for exclude in excludes:
        path = Path(exclude)

        if path.is_absolute():
            raise ValueError(
                "Sandbox exclusions must be relative to the project root."
            )

        if not path.parts:
            raise ValueError(
                "Sandbox exclusions must not refer to the project root."
            )

        if ".." in path.parts:
            raise ValueError(
                "Sandbox exclusions must not escape the project root."
            )

        if path not in normalized:
            normalized.append(path)

    return tuple(normalized)


class ProjectSandbox:
    """Create an isolated temporary copy of a project."""

    _IGNORED_NAMES = (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    )

    def __init__(
        self,
        project_root: Path,
        *,
        excludes: Sequence[Path] = (),
    ) -> None:
        self.project_root = project_root.resolve()
        self.excludes = normalize_sandbox_excludes(excludes)

        self._temporary_directory: tempfile.TemporaryDirectory[str] | None = (
            None
        )
        self.workspace: Path | None = None

    def _ignore(
        self,
        directory: str,
        names: list[str],
    ) -> set[str]:
        relative_directory = Path(directory).relative_to(
            self.project_root
        )

        ignored: set[str] = set()

        for name in names:
            if name in self._IGNORED_NAMES:
                ignored.add(name)
                continue

            relative_path = relative_directory / name

            if relative_path in self.excludes:
                ignored.add(name)

        return ignored

    def __enter__(self) -> Path:
        if not self.project_root.exists():
            raise FileNotFoundError(
                f"Project root does not exist: {self.project_root}"
            )

        if not self.project_root.is_dir():
            raise NotADirectoryError(
                f"Project root is not a directory: {self.project_root}"
            )

        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="mlrepromutate-"
        )

        temporary_root = Path(self._temporary_directory.name)
        self.workspace = temporary_root / self.project_root.name

        shutil.copytree(
            self.project_root,
            self.workspace,
            ignore=self._ignore,
            symlinks=True,
        )

        return self.workspace

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()

        self.workspace = None
        self._temporary_directory = None
