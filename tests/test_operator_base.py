from pathlib import Path

import pytest

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators import MutationOperator


def test_base_operator_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        MutationOperator()


def test_concrete_operator_implements_interface() -> None:
    class ExampleOperator(MutationOperator):
        @property
        def name(self) -> str:
            return "example"

        @property
        def category(self) -> str:
            return "example-category"

        def detect(self, project_root: Path) -> list[MutationCandidate]:
            return [
                MutationCandidate(
                    operator=self.name,
                    category=self.category,
                    target=project_root / "example.txt",
                    description="Example mutation.",
                )
            ]

        def apply(
            self,
            project_root: Path,
            candidate: MutationCandidate,
        ) -> None:
            return None

    operator = ExampleOperator()

    candidates = operator.detect(Path("/tmp/project"))

    assert operator.name == "example"
    assert operator.category == "example-category"
    assert len(candidates) == 1
    assert candidates[0].operator == "example"