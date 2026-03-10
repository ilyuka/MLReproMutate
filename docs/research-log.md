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