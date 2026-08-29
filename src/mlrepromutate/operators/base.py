from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from mlrepromutate.models import MutationCandidate


class MutationOperator(ABC):
    """Base interface for reproducibility mutation operators.

    Subclasses detect candidates and apply one candidate to a project
    workspace. Operators do not manage workspace isolation or restoration.

    Attributes:
        name: Unique operator identifier stored on detected candidates.
        category: Reproducibility-threat category for the operator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique operator name.

        Returns:
            The identifier recorded in ``MutationCandidate.operator``.
        """

    @property
    @abstractmethod
    def category(self) -> str:
        """Return the reproducibility-threat category.

        Returns:
            The category recorded in ``MutationCandidate.category``.
        """

    @abstractmethod
    def detect(self, project_root: Path) -> Iterable[MutationCandidate]:
        """Detect applicable mutation candidates in a project.

        Args:
            project_root: Root directory of the project to inspect.

        Returns:
            An iterable of candidates applicable to the project.
        """

    @abstractmethod
    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        """Apply a mutation to a project workspace.

        Args:
            project_root: Root directory of the workspace to modify.
            candidate: Candidate previously detected by this operator.

        Raises:
            ValueError: The candidate does not belong to the operator or no
                longer matches the workspace.
        """
