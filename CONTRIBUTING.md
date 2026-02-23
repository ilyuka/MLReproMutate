# Contributing to MLReproMutate

MLReproMutate is an early-stage research software project.

Contributions, bug reports, research use cases, documentation improvements,
and suggestions for reproducibility mutation operators are welcome.

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

The development workflow will use a standard Python environment.

```bash
git clone git@github.com:ilyuka/MLReproMutate.git
cd MLReproMutate
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Pull requests

Please:

keep changes focused;
add or update tests where appropriate;
update documentation for user-facing changes;
explain the motivation for significant design changes.