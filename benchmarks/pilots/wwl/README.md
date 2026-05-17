# WWL random-seed pilot

## Repository

- Repository: `BorgwardtLab/WWL`
- Project revision: `107a8dfe3d97d8996753dbdc695f4577514cacbf`
- Research context: accompanying code for the NeurIPS 2019 paper *Wasserstein Weisfeiler-Lehman Graph Kernels*
- Dataset: `MUTAG`

The repository contains experiment scripts intended to reproduce results from
the paper.

The documented minimal experiment command for MUTAG is:

    cd experiments
    python main.py --dataset MUTAG

## Environment

The repository declares Python 3.8 for the experiment environment.

Pilot environment:

    Python 3.8.20

The dependencies from `experiments/requirements.txt` were installed in an
isolated environment before the pilot.

## Mutation

MLReproMutate detected the following explicit random-seed call in
`experiments/main.py`:

    np.random.seed(42)

The controlled mutation was:

    np.random.seed(42) -> np.random.seed(43)

The seed is set immediately before the shuffled stratified evaluation setup:

    np.random.seed(42)
    cv = StratifiedKFold(n_splits=10, shuffle=True)

Because `random_state` is not supplied to `StratifiedKFold`, the global NumPy
random state controls the shuffled partition.

## Validation workflow

The baseline and mutant were evaluated with the same documented experiment:

    cd experiments
    python main.py --dataset MUTAG

MLReproMutate executed the baseline and mutant in separate fresh project
sandboxes.

The baseline completed successfully in approximately 8.95 seconds.

Baseline reported accuracy:

    Final accuracy: 68.421 %

## MLReproMutate result

Outcome:

    SURVIVED

The mutated experiment also completed successfully. Therefore, the selected
workflow did not reject the change from seed 42 to seed 43.

A `SURVIVED` outcome means only that the selected validation workflow completed
successfully after the mutation. It does not by itself imply that the repository
is defective or irreproducible.

## Semantic verification

A separate verification compared the first shuffled stratified split generated
under seeds 42 and 43.

Results:

    train identical: False
    test identical: False

Seed 42 test indices:

    [15, 24, 26, 30, 36, 57, 65, 68, 75, 84, 93, 96, 103, 115, 138, 141, 153, 158, 162]

Seed 43 test indices:

    [2, 7, 9, 18, 24, 32, 34, 43, 46, 47, 49, 54, 77, 84, 108, 120, 129, 151, 153]

The symmetric difference in test membership was 32.

Each test split contained 19 samples. Only 3 test samples were shared between
the two splits.

Therefore, the mutation was not equivalent at the level of the experimental
evaluation partition: changing the seed materially changed which observations
were used for testing.

A controlled manual run of the seed-43 mutant reported:

    Final accuracy: 68.421 %

Thus, in this pilot:

- the random-seed mutation changed the experimental train/test partition;
- the reported accuracy happened to remain unchanged at `68.421 %`;
- the documented workflow still exited successfully;
- MLReproMutate therefore classified the mutation as `SURVIVED`.

This result shows that equality of a reported aggregate metric does not imply
equality of the underlying stochastic experimental execution.

## Raw report

The machine-readable MLReproMutate report is stored at:

    runs/seed-001.json

The raw report is the source of truth for the automated mutation outcome.
The additional split comparison and manual seed-43 execution above were used
only as semantic verification of the survivor.
