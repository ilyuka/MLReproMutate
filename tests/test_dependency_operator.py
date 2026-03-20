from pathlib import Path

import pytest

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator


def test_detects_exact_requirements_pins(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "numpy==2.1.0\n"
        "scikit-learn==1.5.2\n"
        "pytest>=8\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 2

    assert candidates[0].metadata["package"] == "numpy"
    assert candidates[0].metadata["version"] == "2.1.0"
    assert candidates[0].metadata["line_number"] == 1

    assert candidates[1].metadata["package"] == "scikit-learn"
    assert candidates[1].metadata["version"] == "1.5.2"


def test_ignores_non_exact_dependencies(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "numpy>=2\n"
        "pandas~=2.2\n"
        "scipy\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidates = operator.detect(tmp_path)

    assert candidates == []


def test_detects_multiple_requirements_files(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    (tmp_path / "requirements-dev.txt").write_text(
        "pytest==9.1.1\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 2


def test_apply_relaxes_exact_pin(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "numpy==2.1.0\n"
        "scikit-learn==1.5.2\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidate = operator.detect(tmp_path)[1]

    operator.apply(tmp_path, candidate)

    assert requirements.read_text(encoding="utf-8") == (
        "numpy==2.1.0\n"
        "scikit-learn>=1.5.2\n"
    )


def test_apply_changes_only_selected_candidate(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "numpy==2.1.0\n"
        "pandas==2.2.3\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidate = operator.detect(tmp_path)[0]

    operator.apply(tmp_path, candidate)

    assert requirements.read_text(encoding="utf-8") == (
        "numpy>=2.1.0\n"
        "pandas==2.2.3\n"
    )


def test_apply_rejects_candidate_from_other_operator(tmp_path: Path) -> None:
    candidate = MutationCandidate(
        operator="other_operator",
        category="dependency",
        target=Path("requirements.txt"),
        description="Invalid test candidate.",
    )

    operator = RelaxRequirementsPinOperator()

    with pytest.raises(ValueError, match="belongs to operator"):
        operator.apply(tmp_path, candidate)


def test_apply_rejects_changed_target(tmp_path: Path) -> None:
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "numpy==2.1.0\n",
        encoding="utf-8",
    )

    operator = RelaxRequirementsPinOperator()

    candidate = operator.detect(tmp_path)[0]

    requirements.write_text(
        "numpy==2.2.0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="no longer matches"):
        operator.apply(tmp_path, candidate)