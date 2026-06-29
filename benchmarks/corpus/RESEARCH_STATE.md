# MLReproMutate Research State

Last updated: 2026-08-24

This file is the canonical handoff snapshot for continuing the empirical
research work in a new ChatGPT session.

Do not infer methodology from chat history when this file and the frozen
protocol disagree. The repository files and Git tags are the source of truth.

---

## 1. Project

Repository:

    ilyuka/MLReproMutate

Working research title:

    MLReproMutate: Mutation Testing for Reproducibility Safeguards
    in Machine Learning Experiments

Primary goal:

- build and validate MLReproMutate;
- conduct an empirical study on real ML/research repositories;
- prepare an empirical paper/preprint;
- later prepare a JOSS submission.

Core research idea:

Introduce realistic reproducibility-relevant mutations into existing ML
research software and determine whether existing upstream repository validation
workflows detect those changes.

---

## 2. Frozen primary mutation operators

There are exactly four primary mutation operators.

Do not add another primary operator during the current empirical corpus because
of observed KILLED/SURVIVED outcomes.

### dependency-pin

Mutation:

    package==version
        ->
    package>=version

Requires real dependency re-resolution.

### random-seed

Supported forms only:

    random.seed(<integer literal>)
    np.random.seed(<integer literal>)
    numpy.random.seed(<integer literal>)
    torch.manual_seed(<integer literal>)

Mutation:

    N -> N + 1

Not supported:

    random_state=42
    seed=42 function/default parameters
    np.random.seed(variable)
    torch.manual_seed(CONSTANT)
    TensorFlow seed APIs

### data-split

Supported:

    train_test_split(..., stratify=<explicit non-None expression>)

Mutation:

    stratify=<expr>
        ->
    stratify=None

### cv-fold-count

Supported splitters:

    KFold
    StratifiedKFold
    RepeatedKFold
    RepeatedStratifiedKFold

Requires explicit keyword integer literal:

    n_splits=N

Mutation:

    N -> N + 1

---

## 3. Outcome semantics

KILLED:

The selected upstream validation workflow returns non-zero because the mutation
was detected.

SURVIVED:

The selected workflow completes successfully despite the mutation.

SURVIVED does NOT mean the repository is defective or irreproducible.

INVALID:

Generated mutant cannot be meaningfully evaluated.

EQUIVALENT:

Semantic verification shows the mutation did not alter the relevant behavior.

TIMEOUT:

Mutation execution exceeds the predeclared timeout.

ERROR:

Infrastructure/evaluation failure that cannot be interpreted as repository
detection.

---

## 4. Frozen execution rules

These rules must not be relaxed because a repository is inconvenient.

### Fixed revision

Every repository is evaluated at a fixed 40-character Git commit SHA.

### Baseline first

No mutation is evaluated unless the original repository first passes the
selected workflow.

Baseline failure is a screening result, not a mutation outcome.

### Setup

Follow documented upstream setup.

One obvious environment-level compatibility correction is permitted.

After one independent compatibility retry/correction, stop rather than manually
reverse-engineering dependencies until the repository works.

Do not modify upstream research logic to force setup success.

### B02 stage-specific timeouts (amended prospectively before B02-03)

    dependency/setup/install:          900 seconds
    clone/checkout/virtualenv creation: 300 seconds
    baseline validation:                300 seconds
    mutant validation:                  300 seconds
    semantic-verification subprocess:   300 seconds

Only setup/install increased from the original common 300-second bound. Do not
increase any ceiling after observing runtime. The one compatibility correction
rule is unchanged.

### Fresh mutation isolation

One mutation per fresh sandbox.

### Workflow must execute target

Static mutation candidates not exercised by the selected workflow must not be
reported as SURVIVED.

### No study-created primary oracle

A helper created by MLReproMutate may be used for post-hoc semantic
verification, but not as evidence that the upstream repository detected the
mutation.

---

## 5. Protocol versions and Git checkpoints

Calibration snapshot:

    tag: corpus-b01-calibration

Known calibration commit:

    a209640

Tag description:

    Protocol calibration batch B01 before corpus protocol revision

Post-calibration protocol:

    protocol version: 2.0
    tag: corpus-protocol-v2

Important:

B01 records remain schema version 1.

Do not rewrite B01 to make it appear prospectively collected under protocol v2.

All primary post-calibration observations use schema version 2.

Relevant files:

    benchmarks/corpus/PROTOCOL.md
    benchmarks/corpus/SCREENING_SCHEMA.md
    benchmarks/corpus/validate_screening.py
    benchmarks/corpus/screening.jsonl
    tests/test_corpus_screening.py

---

## 6. Research questions after calibration

RQ1:

When realistic reproducibility-relevant mutations are introduced into
machine-learning research software, how often are they detected by existing
repository validation workflows?

RQ2:

How does detection differ by validation-workflow type and by validation-oracle
strength?

Important conceptual distinction:

A documented experiment/example is a validation workflow, but it is not
automatically called a strong safeguard.

---

## 7. Oracle classification in protocol v2

Every selected B02 workflow receives one oracle_kind before mutation execution.

Allowed values:

    assertion
    metric-threshold
    reference-comparison
    completion-only

Classification must be outcome-blind.

---

## 8. Semantic verification in protocol v2

For a SURVIVED primary mutant, attempt post-hoc semantic verification.

Allowed semantic verification states include:

    confirmed-non-equivalent
    unverified

Equivalent mutants require:

    confirmed-equivalent

A study-created semantic verifier does not count as an upstream safeguard.

Primary confirmed mutation-detection denominator:

    KILLED /
    (KILLED + confirmed-non-equivalent SURVIVED)

Screening feasibility must be reported separately.

---

## 9. Candidate-selection rule

Unit of primary analysis:

    one repository-operator pair

For each primary repository/operator case, evaluate exactly one primary
candidate.

If multiple supported candidates exist:

- determine candidate order deterministically;
- use baseline/static executed-path evidence;
- choose before observing mutation outcome;
- do not select candidate based on KILLED/SURVIVED behavior.

Additional candidates may be exploratory but are not part of the primary
repository/operator denominator.

---

# 10. Calibration batch B01

B01 is a completed protocol-calibration batch.

Total:

    10 repository-operator cases

Observed calibration summary:

    10 screened
     7 evaluated
     3 setup-failed
     7 SURVIVED
     0 KILLED

Do not hide the 0 KILLED result.

Do not change operators or select B02 repositories in order to manufacture
KILLED observations.

## B01 cases

### B01-01

Repository:

    snu-causality-lab/efficient-canonical-bounding

Operator:

    dependency-pin

Outcome:

    SURVIVED

Mutation:

    cvxpy==1.8.2 -> cvxpy>=1.8.2

Real dependency resolution changed:

    1.8.2 -> 1.9.2

### B01-02

Repository:

    scikit-learn-contrib/imbalanced-learn

Operator:

    data-split

Result:

    setup-failed

Cause:

External Zenodo dataset could not be obtained reliably.

Mutation not evaluated.

### B01-03

Repository:

    scikit-learn-contrib/MAPIE

Operator:

    random-seed

Outcome:

    SURVIVED

Semantic non-equivalence confirmed:

data / partitions / predictions changed.

### B01-04

Repository:

    wwu-mmll/photonai

Operator:

    cv-fold-count

Outcome:

    SURVIVED

### B01-05

Repository:

    damianhorna/multi-imbalance

Operator:

    data-split

Outcome:

    SURVIVED

Semantic non-equivalence confirmed:

split membership and class distribution changed; one class disappeared from a
split.

### B01-06

Repository:

    KoheiObata/DMM

Operator:

    dependency-pin

Result:

    setup-failed

The documented workflow eventually completed in approximately 474 seconds,
which exceeds the frozen 300-second limit.

Do not retroactively increase timeout.

Mutation not evaluated.

### B01-07

Repository:

    sigeisler/robustness_of_gnns_at_scale

Operator:

    dependency-pin

Result:

    setup-failed

After the allowed compatibility correction, collection failed because required
torch_sparse / torch_geometric dependencies were absent from the documented
setup.

Mutation not evaluated.

### B01-08

Repository:

    ContextLab/hypertools

Operator:

    random-seed

Outcome:

    SURVIVED

Semantic non-equivalence confirmed:

generated values and cluster assignments changed.

### B01-09

Repository:

    sherbold/autorank

Operator:

    random-seed

Outcome:

    SURVIVED

Semantic non-equivalence confirmed:

data, p-value, and mean ranks changed.

### B01-10

Repository:

    BorgwardtLab/P-WL

Operator:

    cv-fold-count

Outcome:

    SURVIVED

Mutation:

    StratifiedKFold n_splits=10 -> 11

Semantic non-equivalence confirmed:

    10-fold count: 10
    11-fold count: 11

Test fold sizes changed and the first held-out partition changed.

---

## 11. Repositories excluded from primary B02 reuse

Do not use B01 repositories again in primary B02:

    snu-causality-lab/efficient-canonical-bounding
    scikit-learn-contrib/imbalanced-learn
    scikit-learn-contrib/MAPIE
    wwu-mmll/photonai
    damianhorna/multi-imbalance
    KoheiObata/DMM
    sigeisler/robustness_of_gnns_at_scale
    ContextLab/hypertools
    sherbold/autorank
    BorgwardtLab/P-WL

Also do not use known development pilots as new primary observations:

    tdsai-lab/cage-agent-authorization
    BorgwardtLab/WWL
    amore-labs/gama
    dmwhyatt/Style-Classification-Analysis

Previously rejected unsupported candidate:

    online-ml/deep-river

Reason:

    seed: int = 42

This is not a supported explicit RNG literal call.

---

# 12. B02 primary corpus design

Target primary B02 corpus:

    40 repository-operator cases

Stratification:

    10 dependency-pin
    10 random-seed
    10 data-split
    10 cv-fold-count

Desired property:

    40 unique repositories

A repository may appear in multiple provisional operator pools during static
screening, but may appear at most once in the final B02 selected frame.

No setup-failed case is replaced after execution begins.

---

## 13. Sampling design

Do NOT select:

- top 40 repositories by stars;
- most popular repositories;
- repositories expected to produce KILLED mutants;
- convenient repositories one-by-one after observing previous outcomes.

Design:

    operator-specific search-derived eligibility frames
        ->
    deterministic cross-pool duplicate resolution
        ->
    fixed-seed random sampling without replacement
        ->
    10 cases per operator
        ->
    frozen 40-case frame
        ->
    execution

Correct methodological description:

    stratified random sampling from operator-specific,
    search-derived eligibility frames

Do NOT claim random sampling from all GitHub research software.

Popularity metrics such as stars/forks are not inclusion criteria.

---

## 14. Static eligibility criteria for pools

Pool construction is STATIC ONLY.

Do not execute tests, examples, environments, or experiments during pool
construction.

Candidate requires:

1. public GitHub repository;
2. identifiable ML/research-software context;
3. paper, DOI, JOSS publication, conference paper, journal article, or clearly
   associated research artifact;
4. current default-branch HEAD fixed at a 40-character SHA;
5. syntactically supported operator candidate;
6. existing upstream validation workflow;
7. static evidence that selected workflow executes mutation target;
8. no known prior MLReproMutate outcome;
9. not a B01/development repository.

Workflow priority:

    1. upstream test exercising target
    2. reproducible CI exercising target
    3. documented validation
    4. documented experiment
    5. documented example

Do not change workflow choice based on presumed mutation-detection strength.

---

# 15. Pool construction status

## random-seed

STATUS:

    SEARCH CLOSED

First broad static pass:

    approximately 70 repository-level possibilities screened
    27 provisional eligible

Fixed second-pass stopping rule:

    exactly 30 NEW distinct repositories screened

Second pass:

    17 eligible
    13 excluded

Current eligible random-seed frame:

    44 repositories

No code was executed.

No mutation outcomes were used.

Do not search additional random-seed repositories unless a factual validation
error invalidates an existing entry.

### robust_mean_estimation correction

Repository:

    AdityaDeshmukh/robust_mean_estimation

Confirmed revision:

    961467ab6eca08ec6b1fb609d578ec8489423291

Target:

    examples/basic.py

Candidate:

    torch.manual_seed(0) -> torch.manual_seed(1)

### random-seed normalization still required

The separate screening chat must return a normalized JSONL containing exactly
44 records.

Expected path after saving:

    benchmarks/corpus/pools/random-seed.jsonl

Before freeze verify:

- exactly 44 records;
- pool_index exactly 1..44;
- all revisions match ^[0-9a-f]{40}$;
- no revision="unknown";
- operator is random-seed for every row;
- oracle_kind is exactly one allowed value;
- no KILLED/SURVIVED prediction language;
- repository values are unique.

### Current second-pass eligible repositories

The following 17 were marked eligible in the fixed 30-repository second pass:

    kLabUM/rrcf
    motiwari/BanditPAM
    josejimenezluna/pyGPGO
    SPFlow/SPFlow
    dicarlolab/CORnet
    eric-mitchell/detect-gpt
    gnina/libmolgrid
    zju3dv/clean-pvnet
    xucong-zhang/ETH-XGaze
    va1shn9v/PromptIR
    pixelite1201/CameraHMR
    bytedance/res-adapter
    ChaoyueSong/MoDA
    ShenhanQian/SpeechDrivesTemplates
    ShenhanQian/UNIF
    kristijanbartol/general-3d-humans
    EvolvingLMMs-Lab/LongVA

### Current random-seed second-pass exclusions

    Accenture/AmpliGraph
        unsupported-mutation-syntax

    dso-org/deep-symbolic-optimization
        insufficient-workflow-target-link

    lanl/Architector
        unsupported-mutation-syntax

    HCLEMINI/FracDimPy
        insufficient-research-reference

    LuChengTHU/dpm-solver
        unsupported-mutation-syntax

    wl-zhao/UniPC
        unsupported-mutation-syntax

    Vchitect/Latte
        unsupported-mutation-syntax

    OpenBMB/MiniCPM
        unsupported-mutation-syntax

    deep-floyd/IF
        unsupported-mutation-syntax

    sthalles/PyTorch-BYOL
        non-portable-upstream-workflow

    dessa-oss/DeepFake-Detection
        private-service-dependent-workflow

    fadel/pytorch_ema
        insufficient-research-reference

    onnx/turnkeyml
        insufficient-research-reference

---

## dependency-pin

STATUS:

    NOT YET CONSTRUCTED / NOT FROZEN

Need the same static-only, outcome-blind pool-construction process.

---

## data-split

STATUS:

    SEARCH CLOSED

Static screening:

    exactly 100 distinct repositories screened

Initial provisional eligibility:

    8 repositories

Post-screen prior-development contamination audit:

    2 excluded

Reasons:

    israelCamperoJurado/GAMA_generalized_island_model_AutoML
        development-lineage-overlap with prior development repository

    Moffran/calibrated_explanations
        prior-development-execution

Final clean eligibility frame:

    6 repositories

No replacement search was performed after the predeclared 100-repository
stopping rule.

Expected path:

    benchmarks/corpus/pools/data-split.jsonl

Under decision D021, current primary stratum cap is:

    min(10, 6) = 6

---

## cv-fold-count

STATUS:

    NOT YET CONSTRUCTED / NOT FROZEN

Need the same static-only, outcome-blind pool-construction process.

---

# 16. Cross-pool duplicates

Do not manually decide which operator receives a repository based on expected
results.

After all four raw pools are complete:

1. save/freeze all raw pools;
2. identify repositories appearing in more than one pool;
3. apply a deterministic outcome-blind duplicate-resolution rule;
4. record that rule before final sampling;
5. only then run fixed-seed sampling.

The exact duplicate-resolution algorithm still needs to be finalized before the
final B02 draw.

---

# 17. Final random selection

Do not perform final random selection until all four operator pools exist and
have passed validation.

Final sampling must:

- use a fixed pseudo-random seed;
- sample without replacement;
- select 10 per operator;
- produce 40 unique repositories after duplicate resolution;
- be reproducible from committed pool files and sampling code.

The exact sampling seed must be written into the sampling script/protocol before
the draw.

---

# 18. Files planned for pool work

Directory:

    benchmarks/corpus/pools/

Expected raw pool files:

    benchmarks/corpus/pools/dependency-pin.jsonl
    benchmarks/corpus/pools/random-seed.jsonl
    benchmarks/corpus/pools/data-split.jsonl
    benchmarks/corpus/pools/cv-fold-count.jsonl

Final selected frame:

    benchmarks/corpus/sampling_frame.jsonl

Do not create/modify final selected frame until all raw pools are frozen.

---

# 19. Current next step

NEXT STEP:

Finish normalization of the already-completed random-seed static frame.

Obtain exactly 44 normalized JSONL records from the separate random-seed
screening chat and save them as:

    benchmarks/corpus/pools/random-seed.jsonl

Then validate that pool locally and commit it.

After random-seed is committed/frozen:

    construct dependency-pin pool

Do NOT:

- execute a random-seed repository;
- draw the random 10 yet;
- search additional random-seed candidates merely to increase pool size;
- choose repositories because they appear likely to be KILLED.

---

# 20. New-chat handoff prompt

Use this in a new ChatGPT chat:

    We are continuing the MLReproMutate empirical study.

    Repository:
    ilyuka/MLReproMutate

    First read these files from the repository:

    benchmarks/corpus/RESEARCH_STATE.md
    benchmarks/corpus/DECISIONS.md
    benchmarks/corpus/PROTOCOL.md
    benchmarks/corpus/SCREENING_SCHEMA.md
    benchmarks/corpus/SAMPLING_PLAN.md

    Also inspect the Git tags:
    corpus-b01-calibration
    corpus-protocol-v2

    Treat those files/tags as the source of truth.

    Continue from the "Current next step" section in RESEARCH_STATE.md.

    Do not change frozen methodology, operator definitions, sampling rules,
    timeout, candidate-selection rules, or corpus denominators merely because
    observed mutation outcomes are inconvenient.

    Give exact shell commands one step at a time.

---

# 21. Working style

Preferred workflow:

    one concrete step
        ->
    run command
        ->
    inspect output
        ->
    record result
        ->
    validate
        ->
    commit
        ->
    next step

Do not generate unnecessary paperwork during execution.

For corpus repositories:

    baseline
        ->
    mutation
        ->
    semantic verification when needed
        ->
    screening ledger
        ->
    validator
        ->
    commit


---

## B02 RAW ELIGIBILITY FRAMES COMPLETE

All four operator-specific searches are closed.

    random-seed:     44 eligible
    dependency-pin:  10 eligible
    data-split:       6 eligible
    cv-fold-count:    3 eligible

Raw cases:

    63

Unique repositories:

    63

Cross-pool duplicates:

    0

Under D021 and D023, planned primary B02 size is:

    10 + 10 + 6 + 3 = 29

Only random-seed requires random subsampling.
No B02 baseline or mutant execution has occurred yet.

Current next step:

    freeze raw frames + sampling algorithm,
    then execute deterministic B02 primary selection.

---

## B02 execution amendment after B02-02, before B02-03

Adopted 2026-08-24. The exact prospective policy is:

    dependency/setup/install:          900 seconds
    clone/checkout/virtualenv creation: 300 seconds
    baseline validation:                300 seconds
    mutant validation:                  300 seconds
    semantic-verification subprocess:   300 seconds

The original common 300-second ceiling censored B02-01 during documented
dependency provisioning. Its original ledger entry and
`runs/B02-01-tslearn-seed.json` remain immutable provenance. Before B02-03,
execute B02-01 fresh under the amended policy and write the distinct completion
report `runs/B02-01-amended-policy-rerun.json`.

B02-02 is complete and must not be rerun. Its setup met the stricter original
bound, so its confirmed-non-equivalent SURVIVED result remains primary.

No sampling-frame field or frozen execution choice changed. The compatibility
retry remains at most one obvious correction. See D024 and the protocol's B02
stage-specific timeout amendment.

Current next execution step:

    B02-01 fresh amended-policy rerun

The first unattended rerun attempt exposed an isolation infrastructure defect:
the host resolver symlink target was absent inside bubblewrap. It produced no
valid empirical observation and does not satisfy the required rerun. Repair and
validate the infrastructure, then execute B02-01 fresh; do not execute B02-03
first.

---

## D025 implementation state after B02-20

D025 is the final B02 policy for normal primary cases beginning at B02-21 and
targeted fresh recovery of earlier canonical setup failures. Its ceilings are
300 seconds clone/checkout/base provisioning, 1800 setup/install, 900 baseline
validation, 900 mutant validation, and 300 semantic verification, with at most
three concrete-failure-directed compatibility corrections.

The normal sequence remains frozen and its next case is B02-21. Already
evaluated cases remain canonical. Specialized-hardware workflow-unavailable
B02-09 is not an environment recovery candidate. S1 reports remain sensitivity
history only. Recovery preserves old reports, replaces one canonical screening
line, uses a fresh unique work directory, and records
`<case>-D025-recovery.json`; infrastructure-invalid attempts do not change
canonical evidence.

User-facing commands:

    python benchmarks/corpus/b02_harness.py recoverable
    python benchmarks/corpus/b02_unattended.py --recover B02-07
    python benchmarks/corpus/b02_unattended.py

Current next normal execution remains B02-21. No case was executed while
implementing the D025 harness support.
