from collections.abc import Sequence
from contextlib import AbstractContextManager
from enum import StrEnum
from pathlib import Path
from types import TracebackType

from mlrepromutate.engine.sandbox import ProjectSandbox
from mlrepromutate.models import MutationCandidate


class ExecutionMode(StrEnum):
    """Supported project execution isolation modes.

    Attributes:
        SANDBOX: Execute in a temporary project copy.
        IN_PLACE: Execute in the supplied project directory.
    """

    SANDBOX = "sandbox"
    IN_PLACE = "in-place"


class ProjectWorkspace(AbstractContextManager[Path]):
    """Provide a project workspace for baseline validation.

    Args:
        project_root: Project directory to expose through the context manager.
        mode: Whether to create a sandbox or use the project in place.
        excludes: Project-relative paths omitted from a sandbox copy.

    Attributes:
        project_root: Resolved source project directory.
        mode: Selected execution mode.
        excludes: Paths omitted from sandbox copies.
        workspace: Active workspace path, or ``None`` outside the context.
    """

    def __init__(
        self,
        project_root: Path,
        mode: ExecutionMode = ExecutionMode.SANDBOX,
        *,
        excludes: Sequence[Path] = (),
    ) -> None:
        self.project_root = project_root.resolve()
        self.mode = mode
        self.excludes = tuple(excludes)
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
            self._sandbox = ProjectSandbox(
                self.project_root,
                excludes=self.excludes,
            )
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
    """Provide a mutation workspace and restore an in-place target.

    In ``IN_PLACE`` mode, only the candidate target's original bytes are
    restored. Side effects produced elsewhere by the validation command are
    not reverted.

    Args:
        project_root: Project directory to expose through the context manager.
        candidate: Candidate whose target may need restoration.
        mode: Whether to create a sandbox or use the project in place.
        excludes: Project-relative paths omitted from a sandbox copy.

    Attributes:
        project_root: Resolved source project directory.
        candidate: Candidate associated with the workspace.
        mode: Selected execution mode.
        excludes: Paths omitted from sandbox copies.
        workspace: Active workspace path, or ``None`` outside the context.
    """

    def __init__(
        self,
        project_root: Path,
        candidate: MutationCandidate,
        mode: ExecutionMode = ExecutionMode.SANDBOX,
        *,
        excludes: Sequence[Path] = (),
    ) -> None:
        self.project_root = project_root.resolve()
        self.candidate = candidate
        self.mode = mode
        self.excludes = tuple(excludes)

        self._workspace_context: ProjectWorkspace | None = None
        self.workspace: Path | None = None

        self._target_path: Path | None = None
        self._original_bytes: bytes | None = None

    def __enter__(self) -> Path:
        self._workspace_context = ProjectWorkspace(
            self.project_root,
            self.mode,
            excludes=self.excludes,
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
