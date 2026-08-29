# Python API

The command-line interface (CLI) is MLReproMutate's primary end-user
interface. See the [CLI reference](cli.md) for its commands and options. A
Python API is also available for programmatic composition and custom mutation
operators.

Before version 1.0, the Python API should be considered provisional. Breaking
Python-API changes, if needed, will be documented in
[CHANGELOG.md](../CHANGELOG.md). Internal helpers not listed on this page are
not part of the supported API.

## Core data model

Import the data-model types from `mlrepromutate.models`:

```python
from mlrepromutate.models import (
    MutationCandidate,
    MutationOutcome,
    MutationResult,
)
```

### `MutationCandidate`

A frozen data class describing a possible mutation detected in a project. Its
fields are:

- `operator`: the unique operator name;
- `category`: the reproducibility-threat category;
- `target`: the mutation target as a path relative to the project root;
- `description`: a human-readable description of the proposed change; and
- `metadata`: operator-specific information used to apply the candidate.

### `MutationOutcome`

A string enum describing the result of mutation evaluation:

- `KILLED`: the selected validation workflow failed after mutation;
- `SURVIVED`: the selected validation workflow succeeded after mutation;
- `INVALID`: the mutation could not be evaluated as the intended change;
- `EQUIVALENT`: the applied mutation did not change the relevant property;
- `TIMEOUT`: mutation validation exceeded its time limit; and
- `ERROR`: evaluation failed because of an unrelated infrastructure or
  framework error.

A `SURVIVED` result means only that the selected validation workflow did not
detect that particular controlled change. It does not prove that the project or
its scientific results are irreproducible.

### `MutationResult`

A frozen data class containing the evaluated `candidate`, its `outcome`, and
optional `duration_seconds`, explanatory `reason`, and evaluation-specific
`metadata`.

## Mutation operator interface

Import the extension interface from the operators package:

```python
from mlrepromutate.operators import MutationOperator
```

Each operator provides:

- `name`, a unique identifier recorded in each candidate;
- `category`, the reproducibility-threat category recorded in each candidate;
- `detect(project_root)`, which inspects a project and returns an iterable of
  `MutationCandidate` objects; and
- `apply(project_root, candidate)`, which modifies the candidate target in the
  supplied workspace.

Operators apply changes but do not provide isolation or restoration. Use the
execution API or workspace utilities when evaluating mutations.

A minimal custom operator has this shape:

```python
from collections.abc import Iterable
from pathlib import Path

from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators import MutationOperator


class CustomOperator(MutationOperator):
    @property
    def name(self) -> str:
        return "custom_operator"

    @property
    def category(self) -> str:
        return "custom_category"

    def detect(self, project_root: Path) -> Iterable[MutationCandidate]:
        # Inspect project_root and return project-relative candidates.
        return []

    def apply(
        self,
        project_root: Path,
        candidate: MutationCandidate,
    ) -> None:
        # Validate the candidate, then modify its target in project_root.
        ...
```

## Built-in mutation operators

Concrete operators are imported from their implementation modules:

- `mlrepromutate.operators.randomness.ChangePythonRandomSeedOperator` changes
  supported literal Python random seeds from `N` to `N + 1`. Its optional
  `python_file` argument restricts detection to one project-relative file.
- `mlrepromutate.operators.dependency.RelaxRequirementsPinOperator` changes
  exact `package==version` entries to `package>=version` in supported
  requirements files. Its optional `requirements_file` argument selects one
  project-relative file; otherwise it inspects top-level
  `requirements*.txt` files.
- `mlrepromutate.operators.data_split.RemoveTrainTestSplitStratificationOperator`
  replaces an explicit, non-`None` `stratify` expression in supported
  scikit-learn `train_test_split` calls with `None`. Its optional `python_file`
  argument restricts detection to one project-relative file.
- `mlrepromutate.operators.evaluation_protocol.ChangeCrossValidationFoldCountOperator`
  increases an explicit literal `n_splits` value by one for supported
  scikit-learn cross-validation splitters. Its optional `python_file` argument
  restricts detection to one project-relative file.

## Execution API

The execution layer is exported from `mlrepromutate.engine`:

```python
from mlrepromutate.engine import (
    BaselineValidationError,
    CommandResolutionError,
    ExecutionMode,
    ExecutionResult,
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
```

- `ExperimentRunner` executes a configured validation command in a project
  workspace and returns an `ExecutionResult` containing the resolved command,
  exit status, output, duration, and timeout status.
- `CommandResolutionError` is raised when a requested `python` or `python3`
  executable cannot be found.
- `MutationEvaluator` validates a baseline and evaluates candidates using an
  `ExperimentRunner` and `ExecutionMode`.
- `BaselineValidationError` is raised when the unmodified baseline fails or
  times out.
- `MutationOrchestrator` detects or accepts candidates, validates the baseline
  once, and then evaluates each selected candidate. If there are no selected
  candidates, it returns an empty list without running the baseline.
- `ExecutionMode.SANDBOX` uses temporary project copies;
  `ExecutionMode.IN_PLACE` uses the supplied project directory.

Evaluation is baseline-first: mutation outcomes are interpreted only after the
unmodified project passes the same validation command. The orchestrator runs
that baseline once before evaluating a non-empty candidate list.

For example:

```python
from pathlib import Path

from mlrepromutate.engine import (
    ExecutionMode,
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
from mlrepromutate.operators.randomness import (
    ChangePythonRandomSeedOperator,
)

project_root = Path("examples/random-seed")
operator = ChangePythonRandomSeedOperator(python_file=Path("experiment.py"))
runner = ExperimentRunner(["python", "validate_guarded.py"])
evaluator = MutationEvaluator(runner, ExecutionMode.SANDBOX)
orchestrator = MutationOrchestrator(evaluator)

results = orchestrator.run(project_root, operator)
for result in results:
    print(result.candidate.description, result.outcome.value)
```

## Workspace utilities

These utilities are also exported from `mlrepromutate.engine`:

```python
from mlrepromutate.engine import (
    MutationWorkspace,
    ProjectSandbox,
    ProjectWorkspace,
)
```

- `ProjectSandbox` is a context manager that copies a project to a temporary
  directory, omitting development directories and configured project-relative
  exclusions. The temporary copy is removed when the context exits.
- `ProjectWorkspace` provides either a temporary sandbox or the original
  project path according to its `ExecutionMode`.
- `MutationWorkspace` additionally preserves and restores the candidate
  target's original bytes in `IN_PLACE` mode, including when validation raises
  an exception or times out.

Sandbox changes do not modify the original project. In-place restoration is
limited to the mutation target: arbitrary files or other side effects created
or changed by the validation command are not reverted. Use in-place execution
only in a disposable or version-controlled workspace where those side effects
are safe.

## Stability

The interfaces listed on this page are the documented, provisional Python
interfaces. The CLI and its documented options are the primary public
end-user interface. Modules, functions, callback aliases, and other helpers not
listed here are internal implementation details and may change without being
treated as supported Python API.
