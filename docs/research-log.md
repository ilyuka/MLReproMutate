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

## 2026-03 — Mutation evaluation pipeline

### Decision

Introduced an evaluation layer that compares validation behavior before and
after applying a reproducibility mutation.

### Evaluation sequence

Each candidate is evaluated using two independent temporary workspaces:

1. an unmodified baseline workspace;
2. a fresh mutated workspace.

The original project is never modified.

### Initial classification

A mutation is classified as `SURVIVED` when the baseline succeeds and the
validation command continues to succeed after mutation.

A mutation is classified as `KILLED` when the baseline succeeds but the
validation command returns a non-zero exit status after mutation.

Mutation execution timeouts are recorded separately as `TIMEOUT`.

### Baseline requirement

A project whose baseline validation fails is not eligible for mutation
classification during that evaluation.

Baseline failures therefore raise a validation error instead of being counted
as killed mutations.

### Current limitation

The initial evaluator uses validation command exit status as the detection
signal.

Future work must address invalid and equivalent mutants and distinguish
failures genuinely caused by the intended reproducibility fault from unrelated
execution failures.

## 2026-04 — First end-to-end reproducibility mutation

### Experiment

Created a controlled dependency-pin fixture and evaluated the same dependency
mutation against two validation configurations.

### Result

Without a dependency safeguard, relaxing an exact dependency pin from
`==1.5.2` to `>=1.5.2` was classified as `SURVIVED`.

After adding a validation safeguard that verifies the exact dependency
constraint, the same mutation was classified as `KILLED`.

### Interpretation

The result demonstrates the intended core semantics of MLReproMutate:
reproducibility mutations can expose safeguards that are absent from an
experiment workflow, while the introduction of an appropriate safeguard
changes the mutation outcome.

### Limitation

This controlled fixture demonstrates safeguard detection rather than actual
package-version drift.

The mutation changes dependency metadata but does not itself force dependency
re-resolution.

## 2026-04 — First end-to-end command-line workflow

### Decision

Added an orchestration layer connecting mutation detection with candidate
evaluation.

The command-line interface now allows a user to provide a project directory
and validation command and receive mutation outcomes without writing Python
integration code.

### Initial scope

The initial CLI currently evaluates the requirements dependency-pin operator
only.

Operator selection and registries will be introduced after additional
mutation categories exist.

### Command execution

Validation commands are parsed into argument sequences and continue to be
executed without a shell.

### Current limitation

Baseline validation is currently performed independently for each candidate.

This prioritizes correctness and isolation in the initial implementation.
Future benchmark work will determine whether baseline reuse is necessary for
performance.

## 2026-04 — Baseline reuse discovered through real-world pilot

### Observation

The first external repository pilot used
`tdsai-lab/cage-agent-authorization` at commit
`978c4e540c8ae7d2aa11efa700c7270d79e71330`.

Its baseline validation command:

`python -m pytest -q`

completed successfully with exit code 0 and required 172.40 seconds.

The initial orchestration implementation repeated this unchanged baseline
before every mutation candidate.

With multiple dependency-pin candidates, this introduced substantial redundant
execution cost.

### Decision

A successful baseline is now validated once per project/operator orchestration
run.

Each mutation candidate continues to execute in its own fresh isolated
sandbox.

### Rationale

Baseline reuse removes redundant validation work without weakening mutation
isolation.

The change was motivated by observed behavior on a real research repository
rather than by synthetic performance assumptions.

## 2026-04 — Progress reporting during real repository evaluation

### Observation

During the first CAGE pilot, a baseline validation required 172.40 seconds.
The CLI produced no output while validation was executing, making a normal
long-running evaluation appear stalled.

### Decision

The CLI now reports baseline validation progress and emits each mutation
result immediately after evaluation.

### Rationale

Long-running research workflows require observable progress. This change was
motivated directly by behavior observed during the first external repository
pilot.

## 2026-04 — Workflow-aware dependency candidate scoping

### Observation

The first completed CAGE pilot detected 10 exact dependency pins across both
`requirements.txt` and `requirements-optional.txt`.

Three candidates (`torch`, `orthogonium`, and `zen-engine`) came from the
optional dependency manifest but were not exercised by the selected
certificate-evaluation workflow.

### Methodological concern

Treating every detected dependency pin as equally applicable to a particular
validation workflow would inflate the mutation-score denominator with
dependencies outside the workflow's execution scope.

### Decision

Dependency mutation detection can now be restricted to a specific
requirements file.

The CLI exposes this through `--requirements-file`.

Candidate progress output also records the source file and line number.

### Interpretation

Mutation detection and mutation applicability are distinct concepts.

A candidate may be syntactically valid while remaining outside the dependency
scope of the validation workflow under study.

## 2026-05 — Machine-readable run provenance

The first external pilot required manual transcription of repository revision,
framework revision, validation configuration, mutation locations, outcomes,
and execution metadata.

MLReproMutate now supports JSON run reports containing:

- project Git revision;
- MLReproMutate Git revision and package version;
- validation command and timeout;
- baseline execution result and duration;
- operator configuration;
- mutation target and metadata;
- mutation outcome and duration;
- captured stdout and stderr;
- aggregate outcome counts.

These JSON reports are intended to serve as the raw source of truth for future
benchmark runs. Derived CSV tables should be generated from these records
rather than manually maintained.

## 2026-05 — Dependency re-resolution design

### Observation

The first machine-readable CAGE run showed that all seven scoped exact-pin
relaxations survived the configured validation workflow.

However, the current dependency operator modifies only the requirements
manifest. It does not resolve or install dependencies after mutation.

### Methodological distinction

Manifest mutation and resolved-environment mutation answer different research
questions.

A relaxed requirement may resolve to the same installed version. Such a case
must not be interpreted as a survived environmental fault.

### Decision

Resolved dependency evaluation will use a fresh isolated Python environment
for the baseline and for every mutant.

Environment construction failures will be classified separately from
validation failures.

If a mutated dependency specification resolves to the same target package
version as the baseline, the mutation will be classified as `EQUIVALENT`.

Only successfully resolved environments with a changed target dependency will
be evaluated as `KILLED`, `SURVIVED`, or `TIMEOUT`.

### Implementation

An isolated virtual-environment resolver was introduced as the first
foundation for resolved dependency experiments.

## 2026-05 — Resolved dependency outcome semantics

Resolved dependency evaluation now distinguishes whether a manifest mutation
actually changes the installed target distribution.

A successful manifest mutation is not automatically considered a survived
reproducibility fault.

Classification rules:

- resolution failure or timeout → `INVALID`;
- unchanged resolved target version → `EQUIVALENT`;
- changed version + successful validation → `SURVIVED`;
- changed version + failed validation → `KILLED`;
- changed version + validation timeout → `TIMEOUT`.

This prevents manifest-only changes from inflating the empirical mutation
score.