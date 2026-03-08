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