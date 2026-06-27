"""Execute untrusted B02 candidate commands inside a fixed bubblewrap sandbox."""

import argparse
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

BWRAP = Path("/usr/bin/bwrap")
B02_WORK_ROOT = Path("/home/ilya/.cache/mlrepromutate/b02")
SYNTHETIC_HOME = Path("/tmp/home")
DEFAULT_ENVIRONMENT = {
    "HOME": str(SYNTHETIC_HOME),
    "LANG": "C.UTF-8",
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "TMPDIR": "/tmp",
}
RESERVED_ENVIRONMENT = frozenset({"HOME", "TMPDIR"})
ENVIRONMENT_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RESOLV_CONF = Path("/etc/resolv.conf")


def _resolved_directory(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {resolved}")
    return resolved


def _require_within(path: Path, root: Path) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"cwd must be inside the B02 work root {root}: {path}") from exc


def parse_environment(values: Sequence[str]) -> dict[str, str]:
    """Parse repeatable NAME=VALUE additions without inheriting host variables."""

    additions: dict[str, str] = {}
    for value in values:
        name, separator, setting = value.partition("=")
        if not separator or ENVIRONMENT_NAME_RE.fullmatch(name) is None:
            raise ValueError(f"environment addition must be NAME=VALUE: {value!r}")
        if name in RESERVED_ENVIRONMENT:
            raise ValueError(f"environment variable {name} is fixed by the sandbox")
        additions[name] = setting
    return additions


def resolver_mount_argv(
    resolv_conf: Path = RESOLV_CONF,
    run_root: Path = Path("/run"),
) -> list[str]:
    """Expose only the resolver file needed by an absolute /etc symlink target."""

    if not resolv_conf.is_symlink():
        return []

    target = resolv_conf.resolve(strict=True)
    try:
        target.relative_to(run_root)
    except ValueError:
        return []
    if not target.is_file():
        raise FileNotFoundError(f"resolver target is not a file: {target}")

    argv: list[str] = []
    parent = target.parent
    missing_parents: list[Path] = []
    while parent != run_root:
        missing_parents.append(parent)
        parent = parent.parent
    for path in reversed(missing_parents):
        argv.extend(("--dir", str(path)))
    argv.extend(("--ro-bind", str(target), str(target)))
    return argv


def bubblewrap_argv(
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str] | None = None,
) -> list[str]:
    """Build the deterministic network-enabled B02 bubblewrap argv."""

    if not command or not all(isinstance(argument, str) for argument in command):
        raise ValueError("command must be a non-empty argv sequence of strings")

    work_root = _resolved_directory(B02_WORK_ROOT, "B02 work root")
    resolved_cwd = _resolved_directory(cwd, "cwd")
    _require_within(resolved_cwd, work_root)

    additions = dict(environment or {})
    for name in additions:
        if ENVIRONMENT_NAME_RE.fullmatch(name) is None:
            raise ValueError(f"invalid environment variable name: {name!r}")
        if name in RESERVED_ENVIRONMENT:
            raise ValueError(f"environment variable {name} is fixed by the sandbox")

    argv = [
        str(BWRAP),
        "--unshare-all",
        "--share-net",
        "--die-with-parent",
        "--new-session",
        "--cap-drop",
        "ALL",
        "--clearenv",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--ro-bind",
        "/etc",
        "/etc",
        *resolver_mount_argv(),
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/home",
        "--dir",
        "/home/ilya",
        "--dir",
        "/home/ilya/.cache",
        "--dir",
        "/home/ilya/.cache/mlrepromutate",
        "--bind",
        str(work_root),
        str(work_root),
        "--dir",
        str(SYNTHETIC_HOME),
        "--dir",
        str(SYNTHETIC_HOME / ".cache"),
    ]
    for name, value in {**DEFAULT_ENVIRONMENT, **additions}.items():
        argv.extend(("--setenv", name, value))
    argv.extend(("--chdir", str(resolved_cwd), "--", *command))
    return argv


def run_isolated(
    command: Sequence[str],
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    **run_options: object,
) -> subprocess.CompletedProcess:
    """Run an argv command in the B02 sandbox and propagate its return code."""

    return subprocess.run(
        bubblewrap_argv(command, cwd, environment),
        cwd=B02_WORK_ROOT,
        shell=False,
        check=False,
        **run_options,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="add a variable to the otherwise cleared environment",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(sys.argv[1:] if argv is None else argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        completed = run_isolated(command, args.cwd, parse_environment(args.env))
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
