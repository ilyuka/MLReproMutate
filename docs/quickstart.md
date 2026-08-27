# Quick start

This tutorial demonstrates the core MLReproMutate workflow using the
CPU-runnable `random-seed` example included in the repository.

## Installation

MLReproMutate requires Python 3.11 or newer.

Clone the repository and install the package:

```bash
git clone https://github.com/ilyuka/MLReproMutate.git
cd MLReproMutate

python -m venv .venv
source .venv/bin/activate

python -m pip install .
```

Confirm that the command-line interface is available:

```bash
mlrepromutate version
mlrepromutate --help
```

## Run a mutation against an unguarded workflow

The example project contains:

```text
examples/random-seed/
├── experiment.py
├── validate_guarded.py
├── validate_unguarded.py
└── README.md
```

`experiment.py` contains an explicit reproducibility-relevant seed:

```python
random.seed(42)
```

Run MLReproMutate against the validation workflow that checks only that the
experiment completes successfully:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py \
  --json-out /tmp/mlrepromutate-random-seed.json
```

MLReproMutate first validates the unmodified baseline. It then detects the
supported seed mutation, evaluates it in an isolated workspace, and reports the
outcome.

For this fixture, the mutation is expected to survive because the unguarded
workflow does not check the exact deterministic result.

## Run against a reproducibility safeguard

Now use the guarded validation workflow:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_guarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

The guarded workflow checks the deterministic value expected for seed `42`.
Changing the seed therefore changes the checked result, and the mutation is
expected to be killed.

## Interpretation

A `KILLED` mutation means that the selected validation workflow detected the
particular controlled change.

A `SURVIVED` mutation means that the selected validation workflow completed
successfully after that change.

Mutation survival must not be interpreted by itself as evidence that a
repository or research result is irreproducible.

## Next steps

The current release provides four operator classes:

- `random-seed`
- `dependency-pin`
- `data-split`
- `cv-fold-count`

See [`cli.md`](cli.md) for command-line options and the
[`examples/`](../examples/) directory for additional fixtures.