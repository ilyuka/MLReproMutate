from contextlib import AbstractContextManager
from enum import StrEnum
from pathlib import Path
from types import TracebackType

from mlrepromutate.engine.sandbox import ProjectSandbox
from mlrepromutate.models import MutationCandidate


class ExecutionMode(StrEnum):
    """Supported project execution isolation modes."""

    SANDBOX = "sandbox"
    IN_PLACE = "in-place"


class ProjectWorkspace(AbstractContextManager[Path]):
    """Provide a project workspace for baseline validation."""

    def __init__(
        self,
        project_root: Path,
        mode: ExecutionMode = ExecutionMode.SANDBOX,
    ) -> None:
        self.project_root = project_root.resolve()
        self.mode = mode
        self._sandbox: ProjectSandbox | None = None
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

        if self.mode is ExecutionMode.SANDBOX:
            self._sandbox = ProjectSandbox(self.project_root)
            self.workspace = self._sandbox.__enter__()
        else:
            self.workspace = self.project_root

        return self.workspace

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._sandbox is not None:
            self._sandbox.__exit__(
                exc_type,
                exc_value,
                traceback,
            )

        self.workspace = None
        self._sandbox = None


class MutationWorkspace(AbstractContextManager[Path]):
    """Provide a workspace and restore in-place mutation targets."""

    def __init__(
        self,
        project_root: Path,
        candidate: MutationCandidate,
        mode: ExecutionMode = ExecutionMode.SANDBOX,
    ) -> None:
        self.project_root = project_root.resolve()
        self.candidate = candidate
        self.mode = mode

        self._workspace_context: ProjectWorkspace | None = None
        self.workspace: Path | None = None

        self._target_path: Path | None = None
        self._original_bytes: bytes | None = None

    def __enter__(self) -> Path:
        self._workspace_context = ProjectWorkspace(
            self.project_root,
            self.mode,
        )
        self.workspace = self._workspace_context.__enter__()

        if self.mode is ExecutionMode.IN_PLACE:
            target = (self.project_root / self.candidate.target).resolve()

            try:
                target.relative_to(self.project_root)
            except ValueError as exc:
                raise ValueError(
                    "Mutation target must be inside the project root."
                ) from exc

            if not target.is_file():
                raise FileNotFoundError(
                    f"Mutation target does not exist: {target}"
                )

            self._target_path = target
            self._original_bytes = target.read_bytes()

        return self.workspace

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if (
                self.mode is ExecutionMode.IN_PLACE
                and self._target_path is not None
                and self._original_bytes is not None
            ):
                self._target_path.write_bytes(self._original_bytes)
        finally:
            if self._workspace_context is not None:
                self._workspace_context.__exit__(
                    exc_type,
                    exc_value,
                    traceback,
                )

            self.workspace = None
            self._workspace_context = None
            self._target_path = None
            self._original_bytes = None
