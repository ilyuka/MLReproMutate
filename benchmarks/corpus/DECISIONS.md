# MLReproMutate Research Decisions

This file records methodological decisions that should not be silently changed
later in response to empirical outcomes.

---

## D001 — Four primary operators

Decision:

The primary mutation set contains exactly:

- dependency-pin
- random-seed
- data-split
- cv-fold-count

Reason:

Representative reproducibility-relevant failure classes while keeping the
initial empirical study interpretable and implementation scope controlled.

Status:

FROZEN.

---

## D002 — Repository/operator pair is the primary unit

Decision:

Primary unit of analysis is one repository-operator pair at one fixed SHA.

Status:

FROZEN.

---

## D003 — Baseline-first

Decision:

A mutation is evaluated only after the original fixed revision successfully
passes the selected upstream workflow.

Baseline failure remains a screening result.

Status:

FROZEN.

---

## D004 — 300-second default timeout

Decision:

Default baseline and mutation validation timeout is 300 seconds unless a
repository-specific timeout is declared before execution.

Do not extend timeout after seeing runtime.

Status:

FROZEN.

---

## D005 — One compatibility correction

Decision:

One obvious environment-level compatibility correction is permitted.

After another independent setup failure, stop screening.

No extended dependency archaeology to force a research repository to run.

Status:

FROZEN.

---

## D006 — B01 is calibration

Decision:

The first ten repository/operator cases are classified as protocol-calibration
batch B01.

Tag:

    corpus-b01-calibration

Known commit:

    a209640

Reason:

B01 exposed that "validation workflow" and "strong safeguard" should not be
treated as synonyms.

Status:

FROZEN historical decision.

---

## D007 — Preserve B01 outcome

Decision:

Do not hide or alter the B01 result:

    7 evaluated
    7 SURVIVED
    0 KILLED
    3 setup-failed

Reason:

Changing operators or corpus retrospectively to create KILLED observations
would introduce outcome-directed researcher degrees of freedom.

Status:

FROZEN.

---

## D008 — Protocol v2 oracle classification

Decision:

Post-calibration records classify workflow oracle strength as exactly one of:

- assertion
- metric-threshold
- reference-comparison
- completion-only

Classification happens before mutation outcome is observed.

Status:

FROZEN.

---

## D009 — Semantic verification of survivors

Decision:

Primary SURVIVED mutants should receive post-hoc semantic verification.

Confirmed non-equivalent survivors are distinguished from unverified survivors.

Study-created semantic verification is not counted as an upstream safeguard.

Status:

FROZEN.

---

## D010 — One primary candidate per repository/operator case

Decision:

Exactly one primary candidate is evaluated per repository/operator case.

When multiple candidates exist, selection is deterministic and based on the
baseline/static executed path before mutation outcome is known.

Status:

FROZEN.

---

## D011 — B02 target size

Decision:

Post-calibration primary corpus target:

    40 cases

Allocation:

    10 dependency-pin
    10 random-seed
    10 data-split
    10 cv-fold-count

Status:

FROZEN unless a pre-execution methodological revision is explicitly documented.

---

## D012 — Do not sample by GitHub popularity

Decision:

Stars, forks, popularity rank, and "top repositories" are not inclusion
criteria.

Reason:

Popularity is a systematic maturity/community bias and is not equivalent to
research usage.

Status:

FROZEN.

---

## D013 — Search-derived operator-specific frames

Decision:

Construct separate static eligibility frames for each operator, then sample
randomly within those frames.

Correct description:

    stratified random sampling from operator-specific,
    search-derived eligibility frames

Do not claim random sampling from all GitHub research software.

Status:

FROZEN.

---

## D014 — Pool construction is static-only

Decision:

During pool construction:

- no environments;
- no tests;
- no examples;
- no baselines;
- no mutants;
- no outcome predictions.

Source, documentation, tests and CI may be inspected statically.

Status:

FROZEN.

---

## D015 — No B01 reuse in primary B02

Decision:

Repositories whose outcomes were observed during B01 are excluded from B02
primary sampling.

Known development pilots are also excluded from new primary observations.

Status:

FROZEN.

---

## D016 — No replacement after execution begins

Decision:

If a selected B02 repository later becomes:

- setup-failed;
- timeout;
- workflow-unavailable;
- otherwise excluded,

it remains in the denominator and is not replaced.

Status:

FROZEN.

---

## D017 — One repository maximum in final B02

Decision:

A repository may occur in multiple provisional operator pools, but the final
40-case B02 frame should contain each repository at most once.

Cross-pool conflicts must be resolved by an outcome-blind deterministic rule
before final random sampling.

Status:

Rule principle FROZEN.

Exact duplicate-resolution algorithm:

TO BE PREDECLARED before final draw.

---

## D018 — Random-seed search stopping rule

Decision:

Random-seed pool construction used:

1. broad first pass of approximately 70 repository-level possibilities;
2. exactly one fixed second pass of 30 new distinct repositories.

The second pass was completed in full rather than stopping when an arbitrary
eligible count was reached.

Result:

    first pass eligible: 27
    second pass eligible: 17
    total eligible frame: 44

Status:

SEARCH CLOSED.

Do not add random-seed candidates merely to enlarge the frame.

---

## D019 — Random selection happens only after all pools

Decision:

Do not draw the final 10 random-seed repositories early.

First complete and freeze:

- dependency-pin pool;
- random-seed pool;
- data-split pool;
- cv-fold-count pool.

Then resolve cross-pool duplicate repositories mechanically.

Then perform one reproducible fixed-seed draw.

Status:

FROZEN.

---

## D020 — Outcome-blindness

Decision:

Repositories must not be:

- selected;
- removed;
- replaced;
- reordered;
- assigned to operators

because they are expected to produce KILLED or SURVIVED mutants.

Status:

FROZEN.


---

## D021 — Operator stratum size under finite eligibility

Decision:

The originally planned 10 primary cases per operator is treated as an upper
target, not as a requirement to continue searching after a predeclared
screening stopping rule has been reached.

For each operator:

    primary_n = min(10, eligible_n)

where eligible_n is the number of cases remaining after:

- the predeclared static screening procedure;
- frozen eligibility criteria;
- prior-calibration/development contamination exclusions;
- deterministic cross-pool duplicate resolution.

No additional repositories are searched merely because an operator-specific
eligibility frame contains fewer than 10 cases.

Reason:

The data-split frame produced fewer than 10 clean eligible repositories after
the predeclared 100-repository stopping rule. Extending search specifically
because the observed eligible count was low would make sampling effort depend
on an intermediate corpus result.

This rule is being declared before construction of the cv-fold-count frame and
therefore before its eligible count is known.

Current implications:

    random-seed:     min(10, 44) = 10 before cross-pool deduplication
    dependency-pin:  min(10, 10) = 10 before cross-pool deduplication
    data-split:      min(10,  6) =  6 before cross-pool deduplication
    cv-fold-count:   min(10,  N) = unknown until its frozen frame is complete

The final B02 sample size is therefore data-dependent within these
prospectively fixed stratum caps and may be smaller than 40.

Status:

FROZEN BEFORE CV-FOLD-COUNT SCREENING.
