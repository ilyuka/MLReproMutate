import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / ".codex" / "rules" / "b02-unattended.rules"
GUIDANCE = ROOT / ".codex" / "b02-unattended.md"
PROMPT = ROOT / ".codex" / "b02-case-prompt.txt"


def policy_decision(*command: str) -> str:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip("Codex CLI is not installed")
    completed = subprocess.run(
        [codex, "execpolicy", "check", "--rules", str(RULES), *command],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)["decision"]


@pytest.mark.parametrize(
    "command",
    [
        ("git", "push", "origin", "main"),
        ("git", "remote", "set-url", "origin", "example"),
        ("git", "config", "remote.origin.url", "example"),
        ("gh", "pr", "create"),
        ("sudo", "true"),
        ("ssh", "example.invalid"),
    ],
)
def test_unattended_policy_forbids_remote_and_privileged_commands(
    command: tuple[str, ...],
) -> None:
    assert policy_decision(*command) == "forbidden"


def test_unattended_policy_allows_local_commit() -> None:
    assert policy_decision("git", "commit", "-m", "local") == "allow"


def test_unattended_guidance_keeps_sandbox_and_automatic_review() -> None:
    text = GUIDANCE.read_text(encoding="utf-8")
    assert "--approve-for-me" in text
    assert "--sandbox workspace-write" in text
    assert "--add-dir /home/ilya/.cache/mlrepromutate/b02" in text
    assert "--dangerously-bypass-approvals-and-sandbox" in text
    assert "Never use" in text
    assert "b02_isolation.py" in text
    assert "run-isolated" in text
    assert "candidate-controlled execution MUST use" in text
    assert "shell=True" in text

    prompt = PROMPT.read_text(encoding="utf-8")
    assert "exactly one B02 case" in prompt
    assert "Do not read unrelated user files" in prompt
    assert "Never use sudo" in prompt
    assert "never\npush it" in prompt
    assert "All candidate-controlled execution MUST go through" in prompt
    assert "b02_isolation.py" in prompt
    assert "run-isolated" in prompt
