from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path

from mlrepromutate.models import MutationCandidate


class MutationOperator(ABC):
    """Base interface for reproducibility mutation operators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique operator name."""

    @property
    @abstractmethod
    def category(self) -> str:
        """Return the reproducibility threat category."""

    @abstractmethod
    def detect(self, project_root: Path) -> Iterable[MutationCandidate]:
        """Detect applicable mutation candidates in a project."""

    @abstractmethod
    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        """Apply a mutation to an isolated project workspace."""