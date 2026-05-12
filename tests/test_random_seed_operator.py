from pathlib import Path

import pytest

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.randomness import (
    ChangePythonRandomSeedOperator,
)


def test_detects_random_seed_literal(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\n"
        "\n"
        "random.seed(42)\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.target == Path("experiment.py")
    assert candidate.operator == "change_python_random_seed"
    assert candidate.category == "randomness"
    assert candidate.metadata["library"] == "random"
    assert candidate.metadata["call"] == "random.seed"
    assert candidate.metadata["original_seed"] == 42
    assert candidate.metadata["mutated_seed"] == 43
    assert candidate.metadata["line_number"] == 3


def test_detects_supported_seed_calls(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\n"
        "import numpy as np\n"
        "import numpy\n"
        "import torch\n"
        "\n"
        "random.seed(1)\n"
        "np.random.seed(2)\n"
        "numpy.random.seed(3)\n"
        "torch.manual_seed(4)\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 4

    assert [
        candidate.metadata["call"]
        for candidate in candidates
    ] == [
        "random.seed",
        "np.random.seed",
        "numpy.random.seed",
        "torch.manual_seed",
    ]

    assert [
        candidate.metadata["mutated_seed"]
        for candidate in candidates
    ] == [
        2,
        3,
        4,
        5,
    ]


def test_ignores_non_literal_seeds(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\n"
        "\n"
        "SEED = 42\n"
        "random.seed(SEED)\n"
        "random.seed(3.14)\n"
        "random.seed('42')\n"
        "random.seed(True)\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()

    assert operator.detect(tmp_path) == []


def test_apply_changes_seed_literal(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\n"
        "\n"
        "random.seed(42)\n"
        "value = 42\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()
    candidate = operator.detect(tmp_path)[0]

    operator.apply(
        tmp_path,
        candidate,
    )

    assert target.read_text(encoding="utf-8") == (
        "import random\n"
        "\n"
        "random.seed(43)\n"
        "value = 42\n"
    )


def test_apply_preserves_unicode_before_seed(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\n"
        'label = "мелодия"; random.seed(42)\n',
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()
    candidate = operator.detect(tmp_path)[0]

    operator.apply(
        tmp_path,
        candidate,
    )

    assert "random.seed(43)" in target.read_text(
        encoding="utf-8"
    )


def test_operator_can_be_scoped_to_one_python_file(
    tmp_path: Path,
) -> None:
    (tmp_path / "experiment.py").write_text(
        "import random\nrandom.seed(42)\n",
        encoding="utf-8",
    )

    (tmp_path / "other.py").write_text(
        "import random\nrandom.seed(100)\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator(
        python_file=Path("experiment.py"),
    )

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].target == Path("experiment.py")
    assert candidates[0].metadata["original_seed"] == 42


def test_scoped_python_file_must_stay_inside_project(
    tmp_path: Path,
) -> None:
    operator = ChangePythonRandomSeedOperator(
        python_file=Path("../experiment.py"),
    )

    with pytest.raises(
        ValueError,
        match="inside the project root",
    ):
        operator.detect(tmp_path)


def test_apply_rejects_stale_candidate(
    tmp_path: Path,
) -> None:
    target = tmp_path / "experiment.py"
    target.write_text(
        "import random\nrandom.seed(42)\n",
        encoding="utf-8",
    )

    operator = ChangePythonRandomSeedOperator()
    candidate = operator.detect(tmp_path)[0]

    target.write_text(
        "import random\nrandom.seed(100)\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="no longer matches",
    ):
        operator.apply(
            tmp_path,
            candidate,
        )


def test_apply_rejects_candidate_from_other_operator(
    tmp_path: Path,
) -> None:
    (tmp_path / "experiment.py").write_text(
        "import random\nrandom.seed(42)\n",
        encoding="utf-8",
    )

    candidate = MutationCandidate(
        operator="other_operator",
        category="randomness",
        target=Path("experiment.py"),
        description="test",
        metadata={},
    )

    operator = ChangePythonRandomSeedOperator()

    with pytest.raises(
        ValueError,
        match="other_operator",
    ):
        operator.apply(
            tmp_path,
            candidate,
        )
