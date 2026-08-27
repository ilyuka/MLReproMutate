# Examples

This directory contains small examples for exercising MLReproMutate mutation
operators and evaluation behavior.

The examples are intended for:

- first-run software evaluation;
- documentation and tutorials;
- automated testing;
- demonstrations of guarded and unguarded validation workflows.

They are separate from the frozen empirical corpus used in the accompanying
research study.

## Random seed

[`random-seed/`](random-seed/) demonstrates mutation of an explicit random
seed.

The experiment contains:

```python
random.seed(42)
```

MLReproMutate changes the supported literal seed to `43`.

The fixture includes an unguarded validation workflow in which the mutation
survives and a guarded workflow in which the mutation is detected.

This is the recommended first example because it is CPU-runnable and uses only
the Python standard library.

Run the unguarded workflow:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

Run the guarded workflow:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_guarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

See [`docs/quickstart.md`](../docs/quickstart.md) for a complete walkthrough.

## Dependency pin

[`dependency-pin/`](dependency-pin/) demonstrates relaxation of an exact
dependency constraint:

```text
package==version
```

to:

```text
package>=version
```

The fixture demonstrates how a dependency mutation can survive a validation
workflow without an appropriate safeguard and be detected after such a
safeguard is introduced.

## Resolved dependency evaluation

[`resolved-dependency/`](resolved-dependency/) exercises dependency evaluation
in which baseline and mutant dependency environments are resolved separately.

This mode is useful when the semantic question is whether relaxing a dependency
constraint actually selects a different installed version rather than merely
changing the requirements-file text.

## Data split

[`data-split/`](data-split/) demonstrates removal of explicit stratification
from a supported `train_test_split` call:

```python
stratify=<expression>
```

to:

```python
stratify=None
```

The fixture provides validation behavior for exercising sensitivity to that
controlled data-partitioning change.

## Cross-validation fold count

[`evaluation-protocol/`](evaluation-protocol/) demonstrates the
`cv-fold-count` mutation operator.

The operator changes an explicit supported cross-validation fold count from
`N` to `N + 1`.

The fixture provides guarded and unguarded validation workflows for exercising
sensitivity to the changed evaluation protocol.

## General command structure

The general CLI form is:

```bash
mlrepromutate run PROJECT \
  --command "VALIDATION COMMAND" \
  --operator OPERATOR
```

For source-level operators, candidate detection can be restricted to one file
with:

```bash
--python-file PATH
```

For dependency mutations, use:

```bash
--requirements-file PATH
```

See [`docs/cli.md`](../docs/cli.md) for the complete command-line reference.

## Interpretation

The examples demonstrate the distinction between execution success and an
explicit reproducibility safeguard.

A `SURVIVED` mutation means that the selected validation workflow completed
successfully after the controlled change.

A `KILLED` mutation means that the selected validation workflow detected that
change through a non-zero validation result.

Mutation survival should not be interpreted by itself as evidence that a
repository or scientific result is irreproducible.