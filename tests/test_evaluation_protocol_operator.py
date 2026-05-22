from pathlib import Path

import pytest

from mlrepromutate.operators.evaluation_protocol import (
    ChangeCrossValidationFoldCountOperator,
)


def test_detects_stratified_kfold_with_literal_n_splits(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        "cv = StratifiedKFold(\n"
        "    n_splits=5,\n"
        "    shuffle=True,\n"
        "    random_state=42,\n"
        ")\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.target == Path("experiment.py")
    assert candidate.category == "evaluation_protocol"
    assert candidate.metadata["splitter"] == "StratifiedKFold"
    assert candidate.metadata["original_n_splits"] == 5
    assert candidate.metadata["mutated_n_splits"] == 6


@pytest.mark.parametrize(
    ("import_line", "call_name", "splitter"),
    [
        (
            "from sklearn.model_selection import KFold as KF",
            "KF",
            "KFold",
        ),
        (
            "import sklearn.model_selection as ms",
            "ms.StratifiedKFold",
            "StratifiedKFold",
        ),
        (
            "from sklearn import model_selection as ms",
            "ms.RepeatedKFold",
            "RepeatedKFold",
        ),
        (
            "import sklearn.model_selection",
            "sklearn.model_selection.RepeatedStratifiedKFold",
            "RepeatedStratifiedKFold",
        ),
    ],
)
def test_detects_supported_import_styles(
    tmp_path: Path,
    import_line: str,
    call_name: str,
    splitter: str,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        f"{import_line}\n"
        f"{call_name}(n_splits=5)\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].metadata["call"] == call_name
    assert candidates[0].metadata["splitter"] == splitter


def test_skips_nonliteral_or_missing_n_splits(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import KFold\n"
        "folds = 5\n"
        "KFold(n_splits=folds)\n"
        "KFold()\n"
        "KFold(5)\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()

    assert operator.detect(tmp_path) == []


def test_skips_unrelated_function_with_same_name(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "def KFold(*, n_splits):\n"
        "    return n_splits\n"
        "\n"
        "KFold(n_splits=5)\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()

    assert operator.detect(tmp_path) == []


def test_apply_changes_only_fold_count(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        'name = "café"\n'
        "cv = StratifiedKFold(\n"
        "    n_splits=5,\n"
        "    shuffle=True,\n"
        "    random_state=42,\n"
        ")\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()
    candidate = operator.detect(tmp_path)[0]

    operator.apply(tmp_path, candidate)

    mutated = source.read_text(encoding="utf-8")

    assert "n_splits=6" in mutated
    assert "shuffle=True" in mutated
    assert "random_state=42" in mutated
    assert 'name = "café"' in mutated


def test_apply_rejects_stale_candidate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        "cv = StratifiedKFold(n_splits=5)\n",
        encoding="utf-8",
    )

    operator = ChangeCrossValidationFoldCountOperator()
    candidate = operator.detect(tmp_path)[0]

    source.write_text(
        "from sklearn.model_selection import StratifiedKFold\n"
        "cv = StratifiedKFold(n_splits=10)\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="no longer matches",
    ):
        operator.apply(tmp_path, candidate)


def test_can_scope_detection_to_one_python_file(
    tmp_path: Path,
) -> None:
    for name in ("first.py", "second.py"):
        (tmp_path / name).write_text(
            "from sklearn.model_selection import KFold\n"
            "KFold(n_splits=5)\n",
            encoding="utf-8",
        )

    operator = ChangeCrossValidationFoldCountOperator(
        python_file=Path("first.py"),
    )

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].target == Path("first.py")
