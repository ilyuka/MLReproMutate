from collections.abc import Callable
from pathlib import Path

from mlrepromutate.engine.evaluator import MutationEvaluator
from mlrepromutate.models import (
    MutationCandidate,
    MutationResult,
)
from mlrepromutate.operators.base import MutationOperator

CandidateStartCallback = Callable[
    [int, int, MutationCandidate],
    None,
]

CandidateResultCallback = Callable[
    [int, int, MutationResult],
    None,
]

BaselinePassedCallback = Callable[[], None]


class MutationOrchestrator:
    """Detect and evaluate mutations for a project."""

    def __init__(self, evaluator: MutationEvaluator) -> None:
        self.evaluator = evaluator

    def run(
        self,
        project_root: Path,
        operator: MutationOperator,
        *,
        on_baseline_passed: BaselinePassedCallback | None = None,
        on_candidate_start: CandidateStartCallback | None = None,
        on_candidate_result: CandidateResultCallback | None = None,
    ) -> list[MutationResult]:
        """Detect and evaluate all candidates produced by an operator."""

        candidates = list(operator.detect(project_root))

        if not candidates:
            return []

        self.evaluator.validate_baseline(project_root)

        if on_baseline_passed is not None:
            on_baseline_passed()

        results: list[MutationResult] = []
        total = len(candidates)

        for index, candidate in enumerate(candidates, start=1):
            if on_candidate_start is not None:
                on_candidate_start(index, total, candidate)

            result = self.evaluator.evaluate_mutation(
                project_root,
                operator,
                candidate,
            )
            results.append(result)

            if on_candidate_result is not None:
                on_candidate_result(index, total, result)

        return results