# Calibrated Explanations data-split pilot

## Repository

- Repository: `Moffran/calibrated_explanations`
- Project revision: `bdb68093d9238bd8c1fb9c07f22f226fa8b70b8b`
- Target workflow: `examples/use_cases/minimal_quickstart.py`
- Dataset: scikit-learn breast cancer dataset

The repository is research software for calibrated and uncertainty-aware
machine-learning explanations and provides a standalone minimal classification
example.

## Environment

The pilot used an isolated Python 3.11 environment with the dependencies
declared by the fixed project revision.

The documented example completed successfully during baseline preflight in
approximately 1.66 seconds.

MLReproMutate's fresh-sandbox baseline completed successfully in approximately
1.28 seconds.

## Mutation operator

Operator:

    remove_train_test_split_stratification

Category:

    data_splitting

The operator changes an explicitly stratified scikit-learn split:

    stratify=<expression>

to:

    stratify=None

while leaving the test size, random state, data, and other split parameters
unchanged.

Two applicable mutation candidates were detected.

## Candidate 1: outer train/test split

Original:

    stratify=dataset.target

Mutation:

    stratify=None

Outcome:

    SURVIVED

Baseline observable output:

    probability: 0.07692307692307693
    probability interval: [0.0, 0.08333333333333333]

Mutant observable output:

    probability: 0.1111111111111111
    probability interval: [0.0, 0.125]

The factual explanation table also changed, including feature conditions and
associated explanation weights.

The workflow nevertheless completed successfully.

## Candidate 2: proper/calibration split

Original:

    stratify=y_train

Mutation:

    stratify=None

Outcome:

    SURVIVED

Baseline observable output:

    probability: 0.07692307692307693
    probability interval: [0.0, 0.08333333333333333]

Mutant observable output:

    probability: 0.125
    probability interval: [0.0, 0.14285714285714285]

The factual explanation table also changed.

This mutation changes the partition between the proper training data and the
calibration data used by the workflow, while the validation command still
completed successfully.

## Semantic verification

A separate verification reproduced the two splitting operations with and
without stratification while keeping the same data, test sizes, and random
state.

For the outer train/test split:

    test membership identical: False
    symmetric difference: 192
    baseline test class counts: [42, 72]
    mutant test class counts: [47, 67]

Both test sets contained 114 samples. Only 18 samples were shared between the
baseline and mutant test sets.

For the proper/calibration split:

    calibration membership identical: False
    symmetric difference: 168
    baseline calibration class counts: [43, 71]
    mutant calibration class counts: [36, 78]

Both calibration sets contained 114 samples. Only 30 samples were shared
between the baseline and mutant calibration sets.

Therefore, neither surviving mutation was equivalent at the level of data
partitioning. Removing stratification materially changed both membership and
class distribution of the affected split.

## Interpretation

Both controlled data-splitting mutations survived the selected workflow.

In both cases, removing explicit stratification changed observable outputs of
the example while the workflow continued to exit successfully.

A `SURVIVED` outcome means that the selected workflow did not reject the
mutation. It does not by itself imply that the repository is defective or
irreproducible.

These results demonstrate that successful execution alone does not guarantee
that a change to a reproducibility-relevant data-splitting policy has been
detected.

## Raw report

The machine-readable MLReproMutate report is stored at:

    runs/data-split-001.json

The raw report is the source of truth for the automated mutation outcomes.
Additional split-membership analysis is used only as semantic verification of
the surviving mutants.
