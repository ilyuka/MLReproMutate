from pathlib import Path

import pytest

from mlrepromutate.engine import ProjectSandbox


def test_sandbox_copies_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    source_file = project / "config.txt"
    source_file.write_text("original", encoding="utf-8")

    with ProjectSandbox(project) as sandbox:
        copied_file = sandbox / "config.txt"

        assert copied_file.exists()
        assert copied_file.read_text(encoding="utf-8") == "original"


def test_sandbox_changes_do_not_modify_original(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    source_file = project / "config.txt"
    source_file.write_text("original", encoding="utf-8")

    with ProjectSandbox(project) as sandbox:
        copied_file = sandbox / "config.txt"
        copied_file.write_text("mutated", encoding="utf-8")

        assert copied_file.read_text(encoding="utf-8") == "mutated"

    assert source_file.read_text(encoding="utf-8") == "original"


def test_sandbox_is_removed_after_exit(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with ProjectSandbox(project) as sandbox:
        sandbox_path = sandbox

        assert sandbox_path.exists()

    assert not sandbox_path.exists()


def test_sandbox_ignores_development_directories(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    git_directory = project / ".git"
    git_directory.mkdir()

    virtual_environment = project / ".venv"
    virtual_environment.mkdir()

    cache_directory = project / "__pycache__"
    cache_directory.mkdir()

    with ProjectSandbox(project) as sandbox:
        assert not (sandbox / ".git").exists()
        assert not (sandbox / ".venv").exists()
        assert not (sandbox / "__pycache__").exists()


def test_sandbox_rejects_missing_project(tmp_path: Path) -> None:
    missing_project = tmp_path / "missing"

    with pytest.raises(FileNotFoundError), ProjectSandbox(missing_project):
        pass


def test_sandbox_rejects_file_as_project(tmp_path: Path) -> None:
    project_file = tmp_path / "project.txt"
    project_file.write_text("not a directory", encoding="utf-8")

    with pytest.raises(NotADirectoryError), ProjectSandbox(project_file):
        pass

def test_sandbox_excludes_requested_directory(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    data = project / "data"
    data.mkdir()
    (data / "dataset.bin").write_bytes(b"large-data")

    (project / "experiment.py").write_text(
        "print('keep me')\n",
        encoding="utf-8",
    )

    with ProjectSandbox(
        project,
        excludes=[Path("data")],
    ) as sandbox:
        assert not (sandbox / "data").exists()
        assert (sandbox / "experiment.py").exists()


def test_sandbox_excludes_nested_path_only(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    data = project / "data"
    data.mkdir()

    raw = data / "raw"
    raw.mkdir()
    (raw / "large.bin").write_bytes(b"large")

    processed = data / "processed"
    processed.mkdir()
    (processed / "small.txt").write_text(
        "keep",
        encoding="utf-8",
    )

    with ProjectSandbox(
        project,
        excludes=[Path("data/raw")],
    ) as sandbox:
        assert not (sandbox / "data" / "raw").exists()
        assert (
            sandbox / "data" / "processed" / "small.txt"
        ).exists()


def test_sandbox_rejects_absolute_exclusion(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(
        ValueError,
        match="relative to the project root",
    ):
        ProjectSandbox(
            project,
            excludes=[tmp_path / "data"],
        )


def test_sandbox_rejects_parent_traversal_exclusion(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(
        ValueError,
        match="escape the project root",
    ):
        ProjectSandbox(
            project,
            excludes=[Path("../data")],
        )
