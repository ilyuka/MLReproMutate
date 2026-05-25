# Data Imbalance evaluation-protocol pilot

## Repository

- Repository: `thecocolab/data-imbalance`
- Revision: `607f784dff11fba9cbf852966dc7631f97d7914f`
- Target: `imbalance/pipeline.py`
- Research context: code accompanying the study on classification metrics
  and class imbalance in neuroscience machine learning.

The project uses stratified cross-validation as part of its evaluation
methodology. Its default non-grouped evaluation protocol constructs:

    StratifiedKFold(n_splits=5)

## Mutation operator

Operator:

    change_cross_validation_fold_count

Category:

    evaluation_protocol

Selected mutation:

    StratifiedKFold(n_splits=5)
                         ↓
    StratifiedKFold(n_splits=6)

The file also contains a separate 10-fold splitter used by the
`single_balanced_split` mode. MLReproMutate detected both candidates and
`--candidate-index 1` was used to evaluate only the active default
cross-validation candidate used by this pilot.

## Validation harness

The pilot used a small external validation harness calling the repository's
public `Pipeline` API on deterministic synthetic binary classification data.

The workload was deliberately reduced to:

    classifiers="lr"
    dataset_balance=[0.5]
    dataset_size=[1.0]
    n_permutations=0
    rand_seed=42
    n_init=1

The cross-validation policy itself was not overridden, so the repository's
default `StratifiedKFold` configuration remained the mutation target.

This harness is a pilot validation workflow created for MLReproMutate. It is
not an upstream repository test or CI safeguard. Therefore this run
demonstrates real-world operator applicability and semantic effect, but should
not be interpreted as evidence about the strength of the repository's own
reproducibility safeguards.

## Baseline

Baseline validation completed successfully in approximately 1.06 seconds.

Observed output:

    fold_count: 5
    accuracy: 0.825
    balanced_accuracy: 0.825
    f1: 0.8266029622551361
    roc_auc: 0.9069444444444444

## Mutant

Mutation:

    n_splits=5 -> n_splits=6

Outcome:

    SURVIVED

Observed output:

    fold_count: 6
    accuracy: 0.8166666666666668
    balanced_accuracy: 0.8166666666666668
    f1: 0.8175204425204425
    roc_auc: 0.8983333333333334

The successful mutation changed the number of cross-validation folds and also
changed all reported evaluation metrics.

The mutant is therefore non-equivalent at both the evaluation-protocol and
observable-output levels.

## Interpretation

The pilot demonstrates that MLReproMutate can identify and execute a
controlled mutation to a cross-validation protocol in real research software.

Changing the default evaluation protocol from five to six stratified folds
materially changed the resulting classification metrics while the validation
workflow continued to complete successfully.

Because the validation command was an MLReproMutate pilot harness rather than
an existing upstream safeguard, the `SURVIVED` result should be interpreted
only within that validation context.

## Raw report

Machine-readable report:

    runs/cv-fold-count-001.json
