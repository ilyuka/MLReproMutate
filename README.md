# MLReproMutate

MLReproMutate is research software for mutation testing of
reproducibility-relevant safeguards in machine-learning research software.

It introduces controlled mutations to experimental and environment choices
and evaluates whether validation workflows already present in a repository
detect those changes.

## Mutation operators

The current release implements four mutation classes used in the empirical
study:

- `random-seed` — changes a supported literal random seed from `N` to `N + 1`;
- `dependency-pin` — relaxes an exact dependency constraint from
  `package==version` to `package>=version`;
- `data-split` — replaces an explicit non-`None` `stratify` argument in a
  supported `train_test_split` call with `None`;
- `cv-fold-count` — changes an explicit cross-validation fold count from
  `N` to `N + 1`.

## Evaluation model

Mutation evaluation is baseline-first. The unmodified project is evaluated
before the mutant, and infrastructure or baseline failures are kept separate
from mutation outcomes.

The software distinguishes mutation execution from semantic verification,
including explicit handling of equivalent dependency mutations.

## Empirical study

The repository contains the frozen empirical evidence underlying the
accompanying empirical preprint, including corpus records, bounded-restoration
evidence, RQ2 metadata, generated accounting tables, and provenance
information.

The empirical corpus is frozen and is not expanded in response to observed
mutation outcomes.

## Development

Install the project in editable mode with `python -m pip install -e .`.

Run the test suite with `python -m pytest -q`.

Run software static checks with `ruff check src tests`.

Inspect the command-line interface with `mlrepromutate --help`.

## Citation

Citation metadata is provided in `CITATION.cff`.

## License

MLReproMutate is released under the MIT License.
