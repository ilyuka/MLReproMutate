from pathlib import Path

import pytest

from mlrepromutate.engine.environment import (
    VirtualEnvironmentResolver,
    normalize_distribution_name,
)


def test_environment_timeout_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="timeout must be positive",
    ):
        VirtualEnvironmentResolver(
            bootstrap_python=Path("/usr/bin/python3"),
            timeout_seconds=0,
        )


def test_distribution_version_returns_none_for_missing_package(
    tmp_path: Path,
) -> None:
    resolver = VirtualEnvironmentResolver(
        bootstrap_python=Path("/usr/bin/python3"),
    )

    assert (
        resolver.distribution_version(
            Path("/usr/bin/python3"),
            "definitely-not-a-real-mlrepromutate-package",
        )
        is None
    )

def test_normalize_distribution_name() -> None:
    assert normalize_distribution_name("scikit-learn") == "scikit-learn"
    assert normalize_distribution_name("Scikit_Learn") == "scikit-learn"
    assert normalize_distribution_name("scikit.learn") == "scikit-learn"