import tomllib
from importlib.metadata import version
from pathlib import Path

import mlrepromutate


def test_version_matches_project_metadata() -> None:
    pyproject = tomllib.loads(
        Path("pyproject.toml").read_text(encoding="utf-8")
    )
    declared_version = pyproject["project"]["version"]

    assert version("mlrepromutate") == declared_version
    assert mlrepromutate.__version__ == declared_version
