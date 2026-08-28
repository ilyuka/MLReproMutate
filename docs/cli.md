# Command-line interface

MLReproMutate provides the `mlrepromutate` command.

```bash
mlrepromutate --help
```

## Interactive setup

Running MLReproMutate without a subcommand starts a guided setup:

```bash
mlrepromutate
```

The interactive workflow asks for the project directory, mutation operator,
optional source or requirements file, validation command, execution mode, and
sandbox exclusions where applicable. It previews detected candidates before
asking whether to start mutation evaluation.

The interactive workflow is intended for human use. For CI, scripts, and
reproducible research protocols, use the explicit `detect` and `run`
subcommands.

## Version

Print the installed MLReproMutate version:

```bash
mlrepromutate version
```

## Detect candidates without execution

Use `detect` to inspect mutation candidates without running project code:

```bash
mlrepromutate detect PROJECT \
  --operator OPERATOR
```

For Python-source operators:

```bash
mlrepromutate detect PROJECT \
  --operator random-seed \
  --python-file experiment.py
```

For dependency pins:

```bash
mlrepromutate detect PROJECT \
  --operator dependency-pin \
  --requirements-file requirements.txt
```

`detect` does not execute the validation workflow, baseline, examples, tests, or
mutants.

## Run mutation evaluation

General form:

```bash
mlrepromutate run PROJECT \
  --command "VALIDATION COMMAND" \
  --operator OPERATOR
```

`PROJECT` is the project directory to evaluate.

The validation command is executed with the selected project directory as its
working directory.

The current release supports four mutation operators:

```text
dependency-pin
random-seed
data-split
cv-fold-count
```

## Select a Python source file

For the `random-seed`, `data-split`, and `cv-fold-count` operators, candidate
detection can be restricted to one Python file:

```bash
--python-file PATH
```

`PATH` is relative to the project root.

Example:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

## Select a dependency file

For the `dependency-pin` operator, candidate detection can be restricted to one
requirements file:

```bash
--requirements-file requirements.txt
```

Example:

```bash
mlrepromutate run PROJECT \
  --command "python validate.py" \
  --operator dependency-pin \
  --requirements-file requirements.txt
```

## Select one detected candidate

If multiple applicable mutation candidates are detected, one candidate can be
selected using its 1-based index:

```bash
--candidate-index 1
```

MLReproMutate reports the total number of detected candidates before running the
selected mutation.

## Execution modes

`run` supports two execution modes:

```text
sandbox
in-place
```

### Sandbox mode

`sandbox` is the default. MLReproMutate creates temporary project copies and
evaluates baseline and mutants there.

```bash
mlrepromutate run PROJECT \
  --operator random-seed \
  --command "pytest -q" \
  --execution-mode sandbox
```

Development directories such as `.git`, `.venv`, `venv`, and common cache
directories are omitted automatically.

Additional paths can be omitted with repeatable `--exclude` options:

```bash
mlrepromutate run PROJECT \
  --operator random-seed \
  --command "pytest -q" \
  --execution-mode sandbox \
  --exclude data \
  --exclude checkpoints
```

Exclusion paths are interpreted relative to the selected project root.
Absolute paths and paths containing parent traversal (`..`) are rejected.

Only exclude files or directories that the selected validation workflow does
not require.

### In-place mode

`in-place` avoids project copying:

```bash
mlrepromutate run PROJECT \
  --operator random-seed \
  --command "pytest -q" \
  --execution-mode in-place
```

Before a mutation, MLReproMutate saves the exact bytes of the mutation target.
The target is restored after evaluation even when validation fails or times out.

The validation command can itself create or modify other project files.
MLReproMutate does not attempt to restore those arbitrary side effects.
Therefore `in-place` mode is intended for disposable, CI, container, or
otherwise safely resettable workspaces.

`--exclude` is only valid in `sandbox` mode.

Resolved dependency evaluation currently does not support `in-place` mode.

## Validation timeout

Set the validation timeout in seconds with:

```bash
--timeout 300
```

The default timeout is 300 seconds.

The baseline and mutant validation commands are subject to this timeout.

## JSON report

A machine-readable JSON report can be written with:

```bash
--json-out report.json
```

Example:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py \
  --json-out report.json
```

## Dependency evaluation modes

The `dependency-pin` operator supports two evaluation modes:

```text
manifest
resolved
```

### Manifest mode

`manifest` is the default mode.

The dependency declaration is mutated from an exact pin such as:

```text
package==version
```

to:

```text
package>=version
```

The selected validation workflow is then evaluated against the mutated project.

A syntactic dependency mutation does not necessarily imply that dependency
resolution would select a different installed version.

### Resolved mode

`resolved` mode creates separate baseline and mutant environments and checks the
resolved version of the target dependency.

Example:

```bash
mlrepromutate run PROJECT \
  --command "python validate.py" \
  --operator dependency-pin \
  --requirements-file requirements.txt \
  --dependency-mode resolved
```

Resolved mode currently requires:

- a `--requirements-file`;
- a Python validation command whose executable name begins with `python`.

This mode allows MLReproMutate to distinguish a syntactically changed
dependency constraint that resolves to the same installed target version from a
mutation that actually changes the resolved dependency environment.

## Operator-specific behavior

### `random-seed`

Targets supported calls with an explicit literal integer seed, including
supported forms of:

```python
random.seed(N)
np.random.seed(N)
numpy.random.seed(N)
torch.manual_seed(N)
```

The mutation is:

```text
N -> N + 1
```

### `dependency-pin`

Targets exact dependency constraints in supported requirements files:

```text
package==version
```

The mutation is:

```text
package==version -> package>=version
```

### `data-split`

Targets supported `train_test_split` calls with an explicit non-`None`
`stratify` argument.

The mutation is:

```python
stratify=<expression>
```

to:

```python
stratify=None
```

### `cv-fold-count`

Targets supported scikit-learn cross-validation splitters with an explicit
literal `n_splits` value.

Supported splitter classes include:

```text
KFold
StratifiedKFold
RepeatedKFold
RepeatedStratifiedKFold
```

The mutation is:

```text
N -> N + 1
```

## Baseline-first evaluation

MLReproMutate validates the unmodified project before interpreting mutation
outcomes.

If the baseline validation command fails or times out, the run is not
interpreted as a normal mutation outcome.

After a successful baseline, each selected mutation is evaluated using the same
validation command. In the default `sandbox` mode this happens in temporary
isolated project copies; `in-place` mode instead uses the supplied workspace
and restores the mutation target after evaluation.

## Outcome interpretation

At the execution level:

- `KILLED` means that the selected validation command returned a non-zero status
  for the mutant.
- `SURVIVED` means that the selected validation command completed successfully
  for the mutant.
- baseline failures are reported separately and do not establish a mutation
  outcome.
- validation timeouts are represented separately.
- additional semantic states may be used where necessary, including dependency
  equivalence handling in resolved evaluation.

A survived mutation does **not** by itself show that a repository or research
result is irreproducible. It shows only that the selected validation workflow
did not detect that particular controlled change.

## Python executable portability

If a validation command starts with exactly `python` or `python3`,
MLReproMutate first resolves that executable from `PATH`. If the requested
alias is unavailable, it tries the other common alias.

For example:

```bash
--command "python validate.py"
```

can work on a system where only `python3` is available.

This fallback is limited to the `python` and `python3` aliases. Arbitrary
executables such as `pytest`, `bash`, and `make` are left unchanged.

## CI usage

A disposable CI checkout can use `in-place` mode to avoid copying the complete
repository:

```yaml
- uses: actions/checkout@v4

- name: Install MLReproMutate
  run: python3 -m pip install mlrepromutate

- name: Run reproducibility mutation check
  run: |
    mlrepromutate run . \
      --operator random-seed \
      --python-file experiment.py \
      --execution-mode in-place \
      --command "pytest -q"
```

The operator is always selected explicitly.

## Related documentation

For a complete first-run example, see:

```text
docs/quickstart.md
```

Additional worked fixtures are available in:

```text
examples/
```

For command details from the installed version, run:

```bash
mlrepromutate run --help
```