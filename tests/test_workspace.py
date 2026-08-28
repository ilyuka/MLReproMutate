from pathlib import Path

import pytest

from mlrepromutate.engine import (
    ExecutionMode,
    MutationWorkspace,
    ProjectWorkspace,
)
from mlrepromutate.models import MutationCandidate


def make_candidate(target: Path) -> MutationCandidate:
    return MutationCandidate(
        operator="test",
        category="test",
        target=target,
        description="Test mutation.",
    )


def test_project_workspace_defaults_to_sandbox(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    source = project / "config.txt"
    source.write_text("original", encoding="utf-8")

    with ProjectWorkspace(project) as workspace:
        assert workspace != project.resolve()

        (workspace / "config.txt").write_text(
            "changed",
            encoding="utf-8",
        )

    assert source.read_text(encoding="utf-8") == "original"


def test_project_workspace_in_place_uses_original_project(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with ProjectWorkspace(
        project,
        ExecutionMode.IN_PLACE,
    ) as workspace:
        assert workspace == project.resolve()


def test_mutation_workspace_restores_exact_bytes_in_place(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    target = project / "experiment.py"
    original = b"# coding: utf-8\r\nvalue = 42\r\n"
    target.write_bytes(original)

    candidate = make_candidate(Path("experiment.py"))

    with MutationWorkspace(
        project,
        candidate,
        ExecutionMode.IN_PLACE,
    ) as workspace:
        (workspace / "experiment.py").write_bytes(
            b"value = 43\n"
        )

    assert target.read_bytes() == original


def test_mutation_workspace_restores_after_exception(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    target = project / "experiment.py"
    original = b"value = 42\n"
    target.write_bytes(original)

    candidate = make_candidate(Path("experiment.py"))

    with pytest.raises(
        RuntimeError,
        match="validation exploded",
    ), MutationWorkspace(
        project,
        candidate,
        ExecutionMode.IN_PLACE,
    ) as workspace:
        (workspace / "experiment.py").write_bytes(
            b"value = 43\n"
        )
        raise RuntimeError("validation exploded")

    assert target.read_bytes() == original


def test_mutation_workspace_sandbox_does_not_modify_original(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    target = project / "experiment.py"
    target.write_text("value = 42\n", encoding="utf-8")

    candidate = make_candidate(Path("experiment.py"))

    with MutationWorkspace(
        project,
        candidate,
        ExecutionMode.SANDBOX,
    ) as workspace:
        (workspace / "experiment.py").write_text(
            "value = 43\n",
            encoding="utf-8",
        )

    assert target.read_text(encoding="utf-8") == "value = 42\n"


def test_mutation_workspace_rejects_target_outside_project(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    outside = tmp_path / "outside.py"
    outside.write_text("value = 42\n", encoding="utf-8")

    candidate = make_candidate(Path("../outside.py"))

    with pytest.raises(
        ValueError,
        match="inside the project root",
    ), MutationWorkspace(
        project,
        candidate,
        ExecutionMode.IN_PLACE,
    ):
        pass
