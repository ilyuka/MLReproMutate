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

`--approve-for-me` is preferred to `--ask-for-approval never`: it retains an
automatic safety review for commands that require approval while remaining
unattended. Network is enabled only inside the sandbox for documented clone and
dependency provisioning. The exec policy is defense in depth; filesystem
isolation, not command-prefix matching, enforces writable-root boundaries.
