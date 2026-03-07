import shutil
import tempfile
from pathlib import Path
from types import TracebackType


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

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self._temporary_directory: tempfile.TemporaryDirectory[str] | None = None
        self.workspace: Path | None = None

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
            ignore=shutil.ignore_patterns(*self._IGNORED_NAMES),
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