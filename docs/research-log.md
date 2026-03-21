# Research Log

This log records experimental observations and design decisions made during
the development and evaluation of MLReproMutate.

---

## 2026-02 — Project initialization

### Goal

Establish the initial public project structure and formalize the research
problem before implementing mutation operators.

### Current hypothesis

Existing tests and CI pipelines in ML research repositories may fail to detect
changes that compromise experimental reproducibility.

### Initial mutation classes

- dependencies;
- dataset/artifact identity;
- configuration;
- preprocessing;
- randomness;
- artifact provenance.

### Current uncertainties

- How frequently will real repositories contain applicable mutation targets?
- How often will mutations be invalid or equivalent?
- Which repository safeguards should count as mutation detectors?
- Can the approach produce useful findings without expensive model training?

### Next experiment

Implement one deterministic dependency-related mutation and evaluate it on a
small CPU-runnable ML example.

### Decision

Introduced separate representations for mutation candidates and mutation
results.

Mutation outcomes explicitly distinguish `KILLED`, `SURVIVED`, `INVALID`,
`EQUIVALENT`, `TIMEOUT`, and `ERROR`.

### Rationale

Infrastructure failures and invalid or equivalent mutants must not be
conflated with successfully detected reproducibility faults, because doing so
would bias future empirical mutation scores.

### Architectural decision

Mutation operators will not restore modified files themselves. Mutations will
later be applied only inside isolated workspaces managed by a sandbox layer.

## 2026-03 — Isolated project sandbox

### Decision

Mutation operators will execute against temporary isolated copies of target
projects instead of modifying the original repository directly.

### Rationale

Mutation testing deliberately introduces potentially destructive changes.
Applying these changes directly to a research repository would create
unnecessary risk and would make reliable cleanup difficult.

The initial implementation therefore creates a temporary project copy,
executes mutations inside that workspace, and removes the workspace after
evaluation.

### Initial implementation

The sandbox excludes development-specific directories such as `.git`,
virtual environments, and Python cache directories.

Symbolic links are preserved rather than followed when creating the sandbox.

### Future consideration

A Git worktree-based sandbox may later be evaluated for large repositories
where copying the entire project becomes a significant performance cost.    

## 2026-03 — Experiment command runner

### Decision

Introduced a generic command runner for executing experiment and validation
commands inside isolated project workspaces.

### Rationale

MLReproMutate must distinguish the act of modifying an experiment from the
mechanism used to execute its validation safeguards.

The runner therefore operates independently from mutation operators and
returns structured execution metadata including the exit status, standard
output, standard error, runtime, and timeout state.

### Safety decision

Commands are executed directly as argument sequences rather than through a
shell.

This avoids unnecessary shell interpretation and makes execution behavior
more predictable.

### Timeout handling

Timeouts are represented explicitly rather than being treated as killed
mutations or generic failures.

Final mutation classification will be handled by a higher-level evaluation
layer.

## 2026-03 — First reproducibility mutation operator

### Implementation

Implemented the first domain-specific reproducibility mutation operator.

The operator detects exact dependency pins in `requirements*.txt` files and
relaxes them from `==version` to `>=version`.

### Research rationale

Exact dependency versions constrain the software environment associated with
an experiment. Relaxing such a constraint models a loss of environment
specificity that may permit future executions to resolve a different package
version.

### Current limitation

Changing a dependency specification does not itself guarantee that the
runtime environment changes.

A later evaluation layer must distinguish mutation of dependency metadata from
actual environment re-resolution.

This operator therefore currently validates mutation detection and
application, not behavioral dependency drift.