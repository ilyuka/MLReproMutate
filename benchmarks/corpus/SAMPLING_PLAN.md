# Primary corpus sampling plan

Protocol version: 2.0
Calibration batch: B01
Primary corpus: B02

## Target size

The post-calibration primary corpus contains exactly 40 preselected
repository-operator cases:

- 10 dependency-pin
- 10 random-seed
- 10 data-split
- 10 cv-fold-count

B01 repositories are excluded from B02 because their outcomes were observed
during protocol calibration.

A repository is used at most once in the B02 primary corpus.

## Selection timing

All 40 repository/operator cases, target files, fixed commit SHAs, and intended
validation workflows are selected before any B02 baseline or mutant is run.

Selection may inspect repository source code, documentation, tests, CI
configuration, publication metadata, and dependency metadata.

Selection must not execute the candidate workflow and must not use mutation
outcomes.

## Candidate discovery

Candidates are discovered using public GitHub source search for syntax supported
by the four frozen MLReproMutate operators.

Randomness searches include:

    np.random.seed(
    numpy.random.seed(
    random.seed(
    torch.manual_seed(

Data-split searches include train_test_split calls with an explicit non-None
stratify argument.

Evaluation-protocol searches include:

    KFold(..., n_splits=<integer>)
    StratifiedKFold(..., n_splits=<integer>)
    RepeatedKFold(..., n_splits=<integer>)
    RepeatedStratifiedKFold(..., n_splits=<integer>)

Dependency searches identify research repositories containing exact
requirements pins of the form package==version.

## Eligibility before execution

A case may enter the frozen frame only when source/document inspection shows:

1. public research repository with identifiable research context;
2. fixed 40-character commit SHA;
3. a syntactically supported mutation candidate;
4. an existing upstream workflow documented by the repository or its CI;
5. the selected workflow is expected from static inspection to execute the
   mutation target;
6. no B01 repository is reused.

Whether setup actually succeeds is deliberately unknown until corpus execution.

## Ordering

Cases are assigned IDs B02-01 through B02-40 before execution.

Execution follows case-ID order.

A setup failure, unavailable workflow, timeout, or other exclusion remains in
the corpus denominator and is not replaced by another repository.

## Outcome blindness

No repository is added, removed, reordered, or replaced because previous B02
mutations were killed or survived.

The four mutation operators and 300-second default timeout remain frozen.
