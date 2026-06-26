# Unattended B02 Codex invocation

This repository requires the Codex CLI's `workspace-write` sandbox, automatic
approval review, the repository as working root, and only the B02 cache as an
additional writable root. Never use `danger-full-access` or
`--dangerously-bypass-approvals-and-sandbox`.

Run one explicitly requested case with:

    codex exec \
      --approve-for-me \
      --sandbox workspace-write \
      --cd /home/ilya/Desktop/projekts/joss/ml-repro-mutate \
      --add-dir /home/ilya/.cache/mlrepromutate/b02 \
      --strict-config \
      -c 'sandbox_workspace_write.network_access=true' \
      -c 'sandbox_workspace_write.writable_roots=["/home/ilya/Desktop/projekts/joss/ml-repro-mutate","/home/ilya/.cache/mlrepromutate/b02"]' \
      - < .codex/b02-case-prompt.txt

The checked-in prompt resolves exactly one case mechanically from the harness.
It states that candidate code is untrusted, unrelated user files and
credentials must not be read, the local rules forbid publication, remote
changes, sudo, and SSH tools, and exactly one local commit is required. Do not
pass `--ignore-rules`.

## Mandatory candidate bubblewrap boundary

The Codex workspace sandbox is the outer automation boundary. In addition, all
untrusted candidate-controlled execution MUST use the deterministic,
repository-owned wrapper:

    python benchmarks/corpus/b02_isolation.py \
      --cwd /home/ilya/.cache/mlrepromutate/b02/<case>/<checkout> \
      --env MPLBACKEND=Agg \
      -- <executable> <argument> ...

The wrapper accepts arbitrary argv after `--` and never invokes a shell. Each
`--env NAME=VALUE` adds a deliberate variable to an otherwise cleared
environment. `HOME=/tmp/home` and `TMPDIR=/tmp` are fixed and cannot be
overridden. Network remains enabled for documented clone/install/workflows.
The wrapper unshares user, PID, IPC, UTS, cgroup, and mount namespaces, drops
all capabilities, provides synthetic `/proc`, `/dev`, `/tmp`, and HOME, mounts
system runtime trees read-only, and exposes only
`/home/ilya/.cache/mlrepromutate/b02` as writable candidate storage. The host
home, `.ssh`, Desktop, and browser/config credential directories are absent.

For timed stages and compact persistent logs, use the harness entry point,
which invokes that same wrapper:

    python benchmarks/corpus/b02_harness.py run-isolated <case-id> \
      --stage <stage> \
      --timeout-class <timeout-class> \
      --cwd /home/ilya/.cache/mlrepromutate/b02/<case>/<checkout> \
      --env MPLBACKEND=Agg \
      -- <executable> <argument> ...

Candidate package installation (including pip operations that may execute
build/setup code), baseline validation, mutant validation, and semantic
verification that imports or executes candidate code must use one of these
forms. Direct execution and `shell=True` are prohibited. Trusted
MLReproMutate bookkeeping, corpus validators, local repository git operations,
and purely static candidate-source inspection may run outside the wrapper.

`--approve-for-me` is preferred to `--ask-for-approval never`: it retains an
automatic safety review for commands that require approval while remaining
unattended. Network is enabled only inside the sandbox for documented clone and
dependency provisioning. The exec policy is defense in depth; filesystem
isolation, not command-prefix matching, enforces writable-root boundaries.
