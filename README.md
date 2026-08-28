# MLReproMutate

MLReproMutate is research software for mutation testing of
reproducibility-relevant safeguards in machine-learning research software.

It introduces controlled changes to experimental and environment choices and
evaluates whether validation workflows already present in a repository detect
those changes.

MLReproMutate is intended for empirical software-engineering research,
machine-learning reproducibility studies, and developers who want to assess
whether existing validation workflows constrain reproducibility-relevant
experimental choices.

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

Confirm the installation:

```bash
mlrepromutate version
mlrepromutate --help
```

For development dependencies:

```bash
python -m pip install -e ".[dev]"
```

## Quick start

The repository includes small CPU-runnable fixtures demonstrating the mutation
workflow.

The `random-seed` fixture can be run without additional machine-learning
dependencies:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

MLReproMutate first validates the unmodified baseline. It then detects the
supported mutation candidate, applies the mutation in an isolated workspace,
runs the same validation command, and reports whether the workflow detected the
change.

For the unguarded fixture, the random-seed mutation survives because the
validation workflow checks only that the experiment completes successfully.

The same mutation can be evaluated against a workflow containing an explicit
reproducibility safeguard:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_guarded.py" \
  --operator random-seed \
  --python-file experiment.py
```

For this fixture, the mutation is killed because the guarded workflow checks the
deterministic output associated with the original seed.

See the [quick-start guide](docs/quickstart.md) for the complete walkthrough.

## Mutation operators

The current release implements four reproducibility-relevant mutation classes.

### `random-seed`

Changes a supported literal random seed from `N` to `N + 1`.

Supported seed-setting forms include calls such as:

```python
random.seed(42)
np.random.seed(42)
numpy.random.seed(42)
torch.manual_seed(42)
```

### `dependency-pin`

Relaxes an exact dependency constraint:

```text
package==version
```

to:

```text
package>=version
```

The resolved-dependency evaluation mode can additionally determine whether the
changed specification actually resolves to a different installed version of the
target dependency.

### `data-split`

Changes a supported `train_test_split` call containing an explicit non-`None`
`stratify` argument:

```python
stratify=<expression>
```

to:

```python
stratify=None
```

### `cv-fold-count`

Changes an explicit literal cross-validation fold count from `N` to `N + 1`.

Supported splitter classes include `KFold`, `StratifiedKFold`,
`RepeatedKFold`, and `RepeatedStratifiedKFold`.

## Evaluation model

Mutation evaluation is baseline-first.

The unmodified project is evaluated before any mutation outcome is interpreted.
A baseline failure or timeout is therefore kept separate from a mutation
result.

After a successful baseline, selected mutations are evaluated in isolated
project workspaces using the same validation command.

At the execution level:

- `KILLED` means that the selected validation workflow returned a non-zero
  status after the mutation was applied.
- `SURVIVED` means that the selected validation workflow completed successfully
  after the mutation was applied.
- baseline failures and validation timeouts are represented separately.
- additional semantic states are used where necessary, including dependency
  equivalence handling during resolved evaluation.

A survived mutation does **not** by itself establish that a repository or its
scientific results are irreproducible. It shows only that the selected
validation workflow did not detect that particular controlled change.

## Machine-readable reports

Use `--json-out` to write a structured report:

```bash
mlrepromutate run examples/random-seed \
  --command "python validate_unguarded.py" \
  --operator random-seed \
  --python-file experiment.py \
  --json-out report.json
```

Reports contain software and project metadata, validation information, mutation
candidate metadata, outcomes, and execution details.

## Documentation

User documentation:

- [Quick start](docs/quickstart.md)
- [Command-line interface](docs/cli.md)
- [Examples](examples/README.md)

Research and design materials:

- [Threat model](docs/threat-model.md)
- [Research log](docs/research-log.md)
- [Related-work notes](docs/related-work.md)

Command-line help for the installed version is also available with:

```bash
mlrepromutate run --help
```

## Examples

The `examples/` directory contains small fixtures for exercising individual
mutation concepts and evaluation behavior.

These fixtures are separate from the frozen empirical corpus and are intended
for documentation, testing, and software evaluation.

See [examples/README.md](examples/README.md).

## Empirical research

MLReproMutate has been used as the experimental instrument in an empirical
study of reproducibility-relevant safeguards in machine-learning research
software.

The repository contains the frozen machine-readable evidence underlying that
study, including corpus records, restoration evidence, study metadata,
generated accounting tables, and provenance information.

The empirical corpus is frozen and is not expanded or modified in response to
observed mutation outcomes.

The software release and frozen empirical artifacts are archived on Zenodo:

**MLReproMutate v0.1.0**
DOI: https://doi.org/10.5281/zenodo.22126120

The accompanying empirical study is available as a preprint:

**Ilya Shulepov. _Mutation Testing for Reproducibility Safeguards in Machine
Learning Research Software: An Empirical Study._ arXiv:2608.27100, 2026.**

https://arxiv.org/abs/2608.27100

## Development

Install the development environment:

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
python -m pytest -q
```

Run static checks:

```bash
ruff check src tests
```

The continuous-integration workflow runs the software checks across supported
Python versions.

## Reporting problems and contributing

Bug reports, usability feedback, research use cases, documentation
improvements, and suggestions for reproducibility mutation operators are
welcome.

Please use the GitHub issue tracker for reproducible bugs or usability
problems:

https://github.com/ilyuka/MLReproMutate/issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and contribution
guidelines.

## Citation

Citation metadata is provided in [CITATION.cff](CITATION.cff).

The archived software release can be cited using:

> Shulepov, Ilya. MLReproMutate, version 0.1.0. Zenodo, 2026.
> https://doi.org/10.5281/zenodo.22126120

## License

MLReproMutate is released under the [MIT License](LICENSE).