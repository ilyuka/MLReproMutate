# Random-seed mutation fixture

This fixture demonstrates mutation of a reproducibility-critical random seed.

The experiment contains the following seed call:

`random.seed(42)`

MLReproMutate changes it to:

`random.seed(43)`

The fixture provides two validation workflows.

## Unguarded validation

`validate_unguarded.py` checks only that the experiment completes and produces
a numeric value in the expected range.

It does not verify the exact deterministic output.

Therefore, the seed mutation is expected to:

`SURVIVE`

## Guarded validation

`validate_guarded.py` checks the exact deterministic value produced when the
experiment uses seed `42`.

Changing the seed to `43` changes that value.

Therefore, the seed mutation is expected to be:

`KILLED`

## Purpose

This fixture demonstrates the difference between a workflow that merely checks
whether an experiment runs successfully and a workflow that actively checks a
reproducibility-sensitive expected result.
