from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.models import MutationResult
from mlrepromutate.operators.base import MutationOperator


class MutationOrchestrator:
    """Detect and evaluate mutations for a project."""

    def __init__(self, evaluator: MutationEvaluator) -> None:
        self.evaluator = evaluator

    def run(
        self,
        project_root: Path,
        operator: MutationOperator,
    ) -> list[MutationResult]:
        """Detect and evaluate all candidates produced by an operator."""

        candidates = list(operator.detect(project_root))

        return [
            self.evaluator.evaluate(
                project_root,
                operator,
                candidate,
            )
            for candidate in candidates
        ]