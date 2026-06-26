import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "benchmarks" / "corpus" / "b02_isolation.py"
WORK_ROOT = Path("/home/ilya/.cache/mlrepromutate/b02")


@pytest.fixture
def synthetic_work_dir() -> Path:
    path = Path(tempfile.mkdtemp(prefix="synthetic-isolation-test-", dir=WORK_ROOT))
    try:
        yield path
    finally:
        shutil.rmtree(path)


def wrapper_command(cwd: Path, *command: str, env: tuple[str, ...] = ()) -> list[str]:
    argv = [sys.executable, str(WRAPPER), "--cwd", str(cwd)]
    for addition in env:
        argv.extend(("--env", addition))
    return [*argv, "--", *command]


def test_synthetic_command_is_isolated_and_work_root_is_writable(
    synthetic_work_dir: Path,
) -> None:
    secret_name = "MLREPRO_SYNTHETIC_HOST_SECRET"
    host_environment = {**os.environ, secret_name: "must-not-cross-boundary"}
    probe = (
        "import json, os, pathlib; "
        "pathlib.Path('created-inside-sandbox').write_text('ok'); "
        "print(json.dumps({'cwd': os.getcwd(), 'home': os.environ['HOME'], "
        "'secret': os.environ.get('MLREPRO_SYNTHETIC_HOST_SECRET'), "
        "'mpl': os.environ.get('MPLBACKEND'), "
        "'ssh': pathlib.Path('/home/ilya/.ssh').exists(), "
        "'desktop': pathlib.Path('/home/ilya/Desktop').exists()}))"
    )

    completed = subprocess.run(
        wrapper_command(
            synthetic_work_dir,
            "/usr/bin/python3",
            "-c",
            probe,
            env=("MPLBACKEND=Agg",),
        ),
        check=False,
        capture_output=True,
        text=True,
        env=host_environment,
    )

    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    assert observed == {
        "cwd": str(synthetic_work_dir),
        "home": "/tmp/home",
        "secret": None,
        "mpl": "Agg",
        "ssh": False,
        "desktop": False,
    }
    assert (synthetic_work_dir / "created-inside-sandbox").read_text() == "ok"


def test_candidate_exit_code_propagates(synthetic_work_dir: Path) -> None:
    completed = subprocess.run(
        wrapper_command(synthetic_work_dir, "/usr/bin/python3", "-c", "exit(23)"),
        check=False,
    )

    assert completed.returncode == 23


def test_virtualenv_executable_inside_work_root_runs(
    synthetic_work_dir: Path,
) -> None:
    virtualenv = synthetic_work_dir / "venv"
    subprocess.run(
        ["/usr/bin/python3", "-m", "venv", str(virtualenv)],
        check=True,
    )

    completed = subprocess.run(
        wrapper_command(
            synthetic_work_dir,
            str(virtualenv / "bin" / "python"),
            "-c",
            "print('venv-ok')",
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == "venv-ok\n"


def test_cwd_outside_fixed_work_root_is_rejected(tmp_path: Path) -> None:
    completed = subprocess.run(
        wrapper_command(tmp_path, "/usr/bin/true"),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "cwd must be inside the B02 work root" in completed.stderr
