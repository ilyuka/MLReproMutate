# Development and Maintenance

## Development setup

MLReproMutate requires Python 3.11 or newer. The package metadata and CI
currently cover Python 3.11, 3.12, and 3.13.

From a repository checkout, create an isolated environment and install the
package with its development dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Repository structure

- `src/mlrepromutate/` contains the installable Python package.
- `src/mlrepromutate/operators/` contains the mutation-operator interface and
  built-in operators.
- `src/mlrepromutate/engine/` contains execution, evaluation, sandbox, and
  workspace orchestration.
- `tests/` contains the automated software test suite.
- `examples/` contains small documentation and software-evaluation fixtures;
  these are separate from the frozen empirical corpus.
- `docs/` contains user, API, design, research, and maintenance documentation.
- `benchmarks/` contains benchmark protocols, corpus records, run evidence,
  and related empirical-study materials, some of which are frozen.
- `paper/` contains paper sources and generated or frozen study assets.

Files under `src/`, `tests/`, `examples/`, and most general documentation are
part of normal software development. Empirical evidence under `benchmarks/`
and associated results and paper assets require separate research-protocol
care; see [Frozen empirical artifacts](#frozen-empirical-artifacts).

## Local validation

Run the checks used by CI:

```bash
python -m pytest -q
ruff check src tests
```

CI runs both checks on Python 3.11, 3.12, and 3.13. Also check the patch for
whitespace errors before submitting it:

```bash
git diff --check
```

## Making changes

1. Make a focused change.
2. Update or add tests for behavioral changes.
3. Update user or API documentation for public-facing changes.
4. Run the tests and Ruff checks above.
5. Update `CHANGELOG.md` when the change is user-visible or otherwise notable.
6. Submit a focused pull request that explains the change and its motivation.

## Adding or changing a mutation operator

Mutation operators implement the `MutationOperator` interface. Its
`detect(project_root)` method inspects a project and returns
`MutationCandidate` objects; its `apply(project_root, candidate)` method
applies one previously detected candidate to the supplied workspace.

An operator should:

- detect only candidates it supports;
- store enough candidate metadata to identify and apply the change safely;
- verify during `apply(...)` that the candidate belongs to the operator and
  still matches the target before changing the workspace;
- keep candidate detection separate from application; and
- preserve the project's existing interpretation of mutation outcomes,
  including `KILLED`, `SURVIVED`, `INVALID`, `EQUIVALENT`, `TIMEOUT`, and
  `ERROR` where applicable.

Tests should cover both detection and application behavior, including rejected
or stale candidates where relevant. See the [Python API documentation](api.md)
for the complete documented interface and built-in operator locations. The
repository does not provide a public plugin registry or registration mechanism.

## Execution and safety model

Evaluation is baseline-first: the unmodified project must pass the selected
validation command before mutation outcomes are interpreted. Sandbox execution
is the default and evaluates mutations in temporary project copies.

In-place execution restores the mutation target after evaluation, including
failed or timed-out validation, but does not undo arbitrary files or other side
effects created by the validation command. Use it only where those side effects
are safe. A `SURVIVED` result means only that the selected workflow did not
detect the controlled change; it does not establish that the repository or its
scientific results are irreproducible. See the [Python API documentation](api.md)
and [threat model](threat-model.md) for details.

## Release process

The package version is stored in `pyproject.toml`. Before a release, prepare
the corresponding user-visible entries in `CHANGELOG.md` and ensure the
release's GitHub tag is exactly `v<package-version>`.

Publishing a GitHub release triggers `.github/workflows/release.yml`. The
workflow checks out that release tag, verifies that it equals `v` followed by
the version in `pyproject.toml`, builds the source and wheel distributions,
runs `python3 -m twine check --strict dist/*`, and uploads the distributions as
a workflow artifact. A dependent job publishes those distributions to PyPI
through the configured `pypi` GitHub environment using PyPI trusted publishing.

The release workflow does not publish to Zenodo. The README and `CITATION.cff`
separately document Zenodo archives for software releases and frozen empirical
artifacts; treat that as repository archival/integration, not an action
performed by `.github/workflows/release.yml`.

## Versioning and compatibility

Package versions are declared in `pyproject.toml`. Record user-visible changes
in `CHANGELOG.md`. Before version 1.0, the Python API is provisional as
documented in the [Python API documentation](api.md); the repository does not
state a stricter compatibility promise.

## Frozen empirical artifacts

Empirical-study artifacts under `benchmarks/` and associated paper results,
tables, figures, preprint assets, and provenance records may represent frozen
research evidence. A normal software contribution must not regenerate, alter,
replace, or reinterpret these artifacts merely as part of a software change.

Consult the [benchmark overview](../benchmarks/README.md), the corpus
[protocol](../benchmarks/corpus/PROTOCOL.md), and the corpus
[research-state handoff](../benchmarks/corpus/RESEARCH_STATE.md) before any
research-artifact work. Such work must follow the applicable frozen protocol
and provenance rules rather than being folded into an unrelated software
change.

## Reporting and maintenance

Use [GitHub issues](https://github.com/ilyuka/MLReproMutate/issues) and the
repository's issue templates for bugs, feature requests, and research or
usability feedback. Contribution expectations are summarized in
[CONTRIBUTING.md](../CONTRIBUTING.md), and community participation is governed
by the [Code of Conduct](../CODE_OF_CONDUCT.md).
