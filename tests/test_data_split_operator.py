from pathlib import Path

import pytest

from mlrepromutate.operators.data_split import (
    RemoveTrainTestSplitStratificationOperator,
)


def test_detects_direct_train_test_split_import(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import train_test_split\n"
        "X_train, X_test = train_test_split(\n"
        "    X,\n"
        "    test_size=0.2,\n"
        "    random_state=42,\n"
        "    stratify=y,\n"
        ")\n",
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.target == Path("experiment.py")
    assert candidate.category == "data_splitting"
    assert candidate.metadata["call"] == "train_test_split"
    assert candidate.metadata["original_stratify"] == "y"
    assert candidate.metadata["mutated_stratify"] == "None"


@pytest.mark.parametrize(
    ("import_line", "call_name"),
    [
        (
            "from sklearn.model_selection import train_test_split as split_data",
            "split_data",
        ),
        (
            "import sklearn.model_selection as model_selection",
            "model_selection.train_test_split",
        ),
        (
            "from sklearn import model_selection as ms",
            "ms.train_test_split",
        ),
        (
            "import sklearn.model_selection",
            "sklearn.model_selection.train_test_split",
        ),
    ],
)
def test_detects_supported_import_styles(
    tmp_path: Path,
    import_line: str,
    call_name: str,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        f"{import_line}\n"
        f"{call_name}(X, y, stratify=y)\n",
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].metadata["call"] == call_name


def test_skips_split_without_enabled_stratification(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import train_test_split\n"
        "train_test_split(X, y)\n"
        "train_test_split(X, y, stratify=None)\n",
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()

    assert operator.detect(tmp_path) == []


def test_skips_unrelated_function_with_same_name(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "def train_test_split(X, y, stratify=None):\n"
        "    return X, y\n"
        "\n"
        "train_test_split(X, y, stratify=y)\n",
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()

    assert operator.detect(tmp_path) == []


def test_apply_replaces_only_stratify_expression(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import train_test_split\n"
        'train_test_split("café", y, test_size=0.2, stratify=y)\n',
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()
    candidate = operator.detect(tmp_path)[0]

    operator.apply(tmp_path, candidate)

    mutated = source.read_text(encoding="utf-8")

    assert (
        'train_test_split("café", y, test_size=0.2, '
        "stratify=None)"
        in mutated
    )
    assert "test_size=0.2" in mutated


def test_apply_rejects_stale_candidate(
    tmp_path: Path,
) -> None:
    source = tmp_path / "experiment.py"
    source.write_text(
        "from sklearn.model_selection import train_test_split\n"
        "train_test_split(X, y, stratify=y)\n",
        encoding="utf-8",
    )

    operator = RemoveTrainTestSplitStratificationOperator()
    candidate = operator.detect(tmp_path)[0]

    source.write_text(
        "from sklearn.model_selection import train_test_split\n"
        "train_test_split(X, y, stratify=labels)\n",
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
            "from sklearn.model_selection import train_test_split\n"
            "train_test_split(X, y, stratify=y)\n",
            encoding="utf-8",
        )

    operator = RemoveTrainTestSplitStratificationOperator(
        python_file=Path("first.py"),
    )

    candidates = operator.detect(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].target == Path("first.py")
