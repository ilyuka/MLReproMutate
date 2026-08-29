# Contributing to MLReproMutate

MLReproMutate is an open-source research software project.

Contributions, bug reports, research use cases, documentation improvements,
and suggestions for reproducibility mutation operators are welcome.

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md). Full setup,
architecture, operator, validation, and release guidance is in the
[development and maintenance guide](docs/development.md). Public Python
interfaces are documented in the [Python API reference](docs/api.md).

## Reporting issues

When reporting a bug, please include:

- operating system;
- Python version;
- MLReproMutate version or commit;
- minimal reproduction steps;
- expected behavior;
- observed behavior.

## Research-related feedback

Feedback is especially useful when it concerns:

- reproducibility failures observed in real ML workflows;
- mutation operators that produce invalid or equivalent mutants;
- missing reproducibility safeguards;
- difficulties applying MLReproMutate to real research repositories.

## Development setup

The development workflow uses a standard Python environment.

```bash
git clone https://github.com/ilyuka/MLReproMutate.git
cd MLReproMutate
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check src tests
```

Do not modify frozen empirical artifacts under `benchmarks/` or associated
paper results as part of an unrelated software contribution. Consult the
[development guide](docs/development.md#frozen-empirical-artifacts) before
working with research artifacts.

## Pull requests

Please:

- keep changes focused;
- add or update tests where appropriate;
- update documentation for user-facing changes; and
- explain the motivation for significant design changes.
