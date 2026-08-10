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

## D004 — Original 300-second default timeout

Decision:

Default baseline and mutation validation timeout is 300 seconds unless a
repository-specific timeout is declared before execution.

Do not extend timeout after seeing runtime.

Status:

FROZEN HISTORICAL POLICY, SUPERSEDED FOR B02 BY D024 AFTER B02-02.

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

---

## D022 — Cross-pool duplicate audit

After freezing the four operator-specific raw eligibility frames, all repository
identifiers were compared across operators before primary sampling.

Raw frames:

    random-seed:     44
    dependency-pin:  10
    data-split:       6
    cv-fold-count:    3

Total repository-operator cases:

    63

Unique repositories:

    63

Cross-pool duplicate repositories:

    0

Therefore no cross-pool duplicate-resolution procedure is required for B02.
No repository was removed or reassigned on the basis of operator overlap.

---

## D023 — B02 primary selection algorithm and random seed

Primary stratum size follows D021:

    primary_n = min(10, eligible_n)

Therefore:

    random-seed:     10 of 44
    dependency-pin:  10 of 10
    data-split:       6 of 6
    cv-fold-count:    3 of 3

Total planned B02 primary corpus:

    29 repository-operator cases

Strata with eligible_n <= 10 are complete enumerations (censuses), not random
subsamples.

Only the random-seed stratum requires random sampling.

Sampling seed phrase:

    MLReproMutate-B02-primary-sampling-v1

For any operator requiring random sampling, derive its integer seed as:

    SHA256("<seed phrase>|<operator>")

Take the first 16 hexadecimal characters of that digest and interpret them as
an unsigned base-16 integer.

Candidates are read in ascending frozen pool_index order.

Use Python random.Random(derived_seed).sample(candidates, primary_n).

After selection, selected records are sorted by their original pool_index for
reporting only. Sorting does not affect selection.

Final B02 case order is:

    1. random-seed
    2. dependency-pin
    3. data-split
    4. cv-fold-count

Within each operator, selected records are ordered by original pool_index.

This decision is frozen before performing the random draw and before executing
any B02 repository.

---

## D024 — Prospective B02 stage-specific timeout amendment

Decision date:

    2026-06-24, after B02-02 and before any B02-03 execution

Decision:

    dependency/setup/install:          900 seconds
    clone/checkout/virtualenv creation: 300 seconds
    baseline validation:                300 seconds
    mutant validation:                  300 seconds
    semantic-verification subprocess:   300 seconds

The compatibility retry remains limited to at most one obvious environment
correction. The frozen sampling frame, repositories, SHAs, candidates,
candidate indices, workflows, mutation magnitudes, workflow kinds, and oracle
kinds remain unchanged.

Reason:

B02-01 demonstrated that the original common 300-second bound can censor
dependency provisioning itself, conflating environment-provisioning cost with
validation execution. This amendment increases only the setup/install ceiling;
the validation ceiling remains 300 seconds.

Provenance treatment:

- preserve the original B02-01 attempt and records without rewriting them;
- perform a fresh, separately recorded B02-01 amended-policy rerun because the
  original attempt was censored solely by setup timeout;
- do not execute B02-03 before that required rerun;
- do not rerun B02-02, because it completed setup within the stricter original
  ceiling and its existing empirical result remains primary.

Status:

FROZEN PROSPECTIVELY BEFORE B02-03.

---

## D025 — Synthetic HOME cache-directory isolation correction

Decision date:

    2026-06-24, after B02-08 and before subsequent B02 execution

Decision:

The bubblewrap synthetic HOME remains `/tmp/home` on the sandbox-private tmpfs
and now includes a writable `/tmp/home/.cache` directory. No real host HOME or
host cache is exposed.

Reason:

B02-08 exposed an isolation artifact when software expanded `~/.cache` and
expected the cache directory to exist before creating a symlink beneath it.

Provenance treatment:

This is a prospective execution-infrastructure correction, not an empirical
compatibility correction or retry under D005. It does not alter the frozen
sample, workflow, candidate, mutation, timeout, or outcome policy, and no
existing screening or run record is rewritten by this change.

Status:

FROZEN PROSPECTIVELY AFTER B02-08.

### S1 — relaxed compatibility sensitivity analysis

After completion of the strict primary random-seed execution pass, a secondary
sensitivity analysis may be run for primary cases that were not mutation-evaluable
because the documented workflow failed under the bounded compatibility policy.

S1 does not replace or modify primary outcomes.

S1 permits at most two error-directed compatibility corrections per fresh case run.

A correction must be directly motivated by an observed execution error and may only:
- install an evidently required missing runtime dependency;
- select a compatible release/range of an upstream dependency;
- normalize an environment/path representation without changing workflow semantics.

S1 must not:
- edit candidate source except for the frozen mutation;
- change the selected candidate;
- change the validation oracle;
- weaken or skip tests/checks;
- substitute CPU for a workflow that semantically requires CUDA;
- increase frozen setup or validation timeouts;
- search arbitrary fixes after two corrections.

Primary strict results remain canonical and are reported separately from S1 results.

### B02-20 corrective primary rerun

The first B02-20 primary execution is retained as audit history but is
procedure-invalid for primary inference.

Its single compatibility correction attempted to provision the repository's
documented Python 3.6.1 runtime via a Miniconda distribution artifact that
returned HTTP 404. Subsequent verification established that a valid official
Linux x86_64 Miniconda bootstrap remains available in the Anaconda archive.

Therefore the observed 404 reflected an incorrectly selected provisioning
artifact rather than evidence that the documented historical runtime was
unavailable.

B02-20 will receive one fresh corrective primary rerun with:
- identical frozen repository revision;
- identical dependency mutation candidate;
- identical workflow and oracle;
- identical 900-second setup and 300-second validation limits;
- the same maximum of one error-directed compatibility correction.

The previous B02-20 report is preserved unchanged for audit history. The
corrective rerun, if methodologically valid, becomes the canonical primary
B02-20 record. This correction does not alter the execution policy or sample.

## D025 — B02 bounded compatibility-recovery execution policy

D025 was adopted after completion of B02-01 through B02-20 and before any
execution of B02-21 through B02-29.

### Trigger

After reconciliation of the prospectively amended B02-01 execution, only
5 of the first 20 frozen B02 cases reached mutation evaluation. Fourteen were
setup-failed and one was workflow-unavailable.

This amendment is motivated by the high PRE-MUTATION non-evaluability rate,
which substantially limits the usable empirical denominator.

The amendment is not motivated by whether observed mutations were KILLED,
SURVIVED, or equivalent. Repository selection, frozen revisions, mutation
candidates, workflows, and validation oracles remain unchanged.

The complete B02 sample of 29 cases was frozen before these executions.

### Scope

D025 becomes the final B02 execution policy for:

1. all not-yet-executed B02 cases beginning with B02-21; and
2. fresh recovery executions of previously non-evaluable B02 cases.

Cases that already reached mutation evaluation under an earlier stricter
policy remain valid and are not rerun because they already satisfy a strict
subset of D025.

Previous strict, amended, corrective, and S1 reports are preserved as audit
history. Existing S1 sensitivity results do not automatically become canonical
D025 primary results.

### Time limits

- clone / checkout / base environment provisioning: 300 seconds
- setup / dependency installation: 1800 seconds
- baseline validation: 900 seconds
- mutant validation: 900 seconds
- semantic-verification subprocess: 300 seconds

### Bounded compatibility recovery

After the documented/native setup is attempted, at most THREE error-directed
compatibility corrections may be applied.

A correction may only respond to a concrete observed setup or baseline
failure. Corrections must not be chosen using mutation outcome information.

Permitted correction classes are:

1. Historical runtime provisioning when supported by repository documentation,
   CI configuration, package metadata, or other frozen upstream evidence.
   Publicly archived interpreter distributions and package channels may be used
   to obtain that documented runtime.

2. A compatible version or version range for a NON-TARGET dependency when a
   concrete packaging, interpreter, ABI, or runtime incompatibility is observed.

3. Installation of a missing runtime, test, or validation dependency when its
   absence is demonstrated by the selected workflow failure.

4. Environment-only normalization such as cache, path, HOME, XDG, locale, or
   equivalent execution-environment configuration that does not alter research
   semantics.

Each intentional environment/dependency adaptation after an observed failure
counts as one correction. No more than three corrections are allowed.

Historical-runtime provisioning may use an appropriate public archival channel
as part of that single runtime-provisioning correction when needed to obtain
the exact documented interpreter.

### Symmetry

Any compatibility correction required for an evaluated case must be applied
equivalently to the independently provisioned baseline and mutant environments.

The mutation itself remains the only intended baseline-versus-mutant
difference.

### Forbidden adaptations

D025 does NOT permit:

- repository source patches for compatibility;
- changing the frozen mutation candidate;
- changing the selected workflow;
- changing the oracle;
- skipping tests or validation steps;
- weakening assertions;
- substituting a different experiment;
- increasing timeouts beyond D025;
- outcome-directed setup changes;
- constraining the TARGET dependency in a way that cancels or weakens the
  frozen mutation;
- CPU substitution for a workflow that genuinely requires unavailable
  specialized hardware.

A genuinely unavailable required GPU or other specialized resource remains
workflow-unavailable.

### Infrastructure failures

System suspend, DNS failure, transient network interruption, broken outer
sandboxing, or equivalent infrastructure failures are not empirical outcomes
and do not consume a compatibility correction.

Such attempts are retained as infrastructure-invalid audit history and may be
rerun fresh.

### Canonicalization of recovery runs

A valid D025 recovery execution of a previously non-evaluable case supersedes
the earlier non-evaluable record as the canonical B02 record.

The previous report must remain unchanged as audit history.

The existing case line in screening.jsonl is replaced; a duplicate case line
must never be appended.

If a D025 recovery remains non-evaluable after the bounded recovery budget,
that D025 result becomes the canonical final primary classification.

### Analysis

The final mutation-detection analysis uses canonical D025-compatible results.

Earlier strict executability remains reportable separately as a descriptive
sensitivity result on environment/setup fragility.

## D026 — Target-execution classification clarification

D026 was adopted after B02-25 and before execution of B02-26.

B02-25 exposed a classification case not explicitly represented by the
existing execution bookkeeping: the selected completion-only workflow returned
exit code 0, but internal trial failures prevented execution from reaching the
frozen mutation target.

This clarification does not change the frozen workflow oracle.

For a completion-only workflow:

- process return code 0 remains a passed baseline oracle;
- process return code nonzero remains a failed baseline oracle.

However, mutation evaluation additionally requires evidence that execution
reached the frozen mutation target. If the baseline workflow satisfies its
declared oracle but the frozen target is not exercised, the mutation is not
applied and the case is classified as workflow-unavailable for mutation
evaluation, with the reason recorded as target-not-exercised.

Such a case must not be classified as setup-failed merely because internal
errors were swallowed by the selected workflow.

This clarification changes no repository, revision, candidate, workflow,
oracle, timeout, or D025 compatibility-correction budget and is independent of
mutation outcome.

---

## D027 — Post-stage-one manual historical-environment restoration sensitivity protocol

D027 was adopted on 2026-07-25 after completion of all canonical B01 and B02
stage-one execution attempts.

### Trigger

Stage-one execution is complete:

- B01: 10 intended, 7 mutation-evaluated, 3 setup-failed;
- B02: 29 intended, 6 mutation-evaluated, 21 setup-failed, and
  2 workflow-unavailable.

The large PRE-MUTATION non-evaluability count motivates a deeper investigation
of whether historically plausible software environments can restore valid
baselines.

D027 is motivated by executability attrition, not by whether previously
observed mutations were KILLED, SURVIVED, or equivalent.

### Inferential role

D027 is a secondary manual-restoration sensitivity analysis.

It does NOT replace, supersede, or rewrite canonical B01 or D025 B02 results.

In particular:

- D025 remains the final primary B02 execution policy;
- canonical stage-one screening.jsonl records remain unchanged by D027;
- previous reports remain immutable audit history;
- D027-restored mutation outcomes must be reported separately from the primary
  D025 mutation-detection estimate;
- B01 remains a calibration batch and is not retrospectively converted into B02
  primary evidence.

A secondary expanded/sensitivity estimate may be reported from D027 results,
but it must be explicitly labelled as post-stage-one manual restoration.

### Frozen restoration cohort

The D027 cohort is frozen before any D027 restoration execution.

It contains every case whose canonical stage-one classification is
setup-failed:

B01:

- B01-02
- B01-06
- B01-07

B02:

- B02-03
- B02-05
- B02-06
- B02-07
- B02-08
- B02-10
- B02-11
- B02-12
- B02-13
- B02-15
- B02-16
- B02-17
- B02-18
- B02-20
- B02-21
- B02-22
- B02-23
- B02-24
- B02-27
- B02-28
- B02-29

Total:

    24 setup-failed cases

The machine-readable frozen cohort is:

    benchmarks/corpus/d027_restoration_cohort.jsonl

B02-09 and B02-25 are excluded because their canonical classifications are
workflow-unavailable rather than setup-failed:

- B02-09 requires unavailable CUDA hardware;
- B02-25 passed its completion-only oracle but did not exercise the frozen
  mutation target.

No replacement repositories may be added.

Every one of the 24 cohort cases is intended for a D027 attempt. Execution
order is operational only and must not be used to drop difficult cases or
retain only successfully restored cases.

### Frozen empirical identity

D027 must preserve for every case:

- repository;
- frozen revision;
- frozen mutation operator;
- frozen mutation candidate;
- selected workflow;
- selected oracle.

Repository source or test compatibility patches are not permitted.

The frozen mutation itself remains the only permitted source change.

### Restoration objective

The restoration phase first attempts to construct a historically plausible
environment in which the frozen baseline workflow is valid.

Mutation outcome information must not be used while constructing that
environment.

The mutation must not be applied until:

1. the baseline satisfies the frozen workflow oracle; and
2. execution reaches the frozen mutation target when target-execution evidence
   is required under D026.

### Evidence hierarchy

Historical-environment decisions should preferentially use:

1. documentation at the frozen repository revision;
2. CI configuration at the frozen revision;
3. requirements, setup, environment, lock, or package metadata;
4. contemporaneous public package/release metadata;
5. concrete observed setup or baseline failures.

The canonical pre-D027 failure record is itself valid concrete evidence and may
motivate the first D027 correction. A known D025 failure does not have to be
reproduced merely to observe the same error again.

### D027 time limits

Per fresh execution attempt:

- clone / checkout / base provisioning: 300 seconds
- setup / dependency installation: 3600 seconds
- baseline validation: 1800 seconds
- mutant validation: 1800 seconds
- semantic verification: 300 seconds

These larger limits belong only to D027 sensitivity analysis and do not
retroactively alter B01 or D025 classifications.

### Bounded manual compatibility recovery

At most EIGHT substantive error-directed compatibility corrections may be
applied per case.

A historical-runtime pivot counts as one of these eight corrections.

Every correction must be justified by either:

- a concrete canonical pre-D027 failure; or
- a concrete failure observed during the current D027 restoration.

A correction is one documented compatibility hypothesis/action. Unrelated
adaptations must not be bundled together merely to evade the correction limit.

Permitted correction classes are:

1. Provisioning a historically supported Python/runtime version using
   repository evidence and public archival distributions or channels.

2. Selecting a compatible version or version range for a NON-TARGET dependency
   after a concrete interpreter, packaging, ABI, API, or runtime
   incompatibility.

3. Installing a concretely demonstrated missing runtime, test, validation, or
   build dependency.

4. Installing environment/build prerequisites such as compilers, development
   headers, or build tooling required to install the historical dependency
   stack.

5. Environment-only normalization such as PATH, PYTHONPATH, HOME, XDG, cache,
   locale, backend, or equivalent configuration that does not change the
   research workflow semantics.

6. Recovering the SAME documented public dataset/model/artifact from its
   canonical source or a provenance-preserving official/public mirror when the
   original transport location is unavailable. The source, provenance, and
   available checksum/hash information must be recorded. Substitution with a
   different dataset/model/artifact is forbidden.

Infrastructure-only failures do not consume the eight-correction budget.

### Forbidden adaptations

D027 does NOT permit:

- repository source compatibility patches;
- test patches;
- changing the frozen mutation candidate;
- changing the frozen workflow;
- changing the frozen oracle;
- skipping tests or validation steps;
- weakening assertions;
- reducing or substituting the frozen experiment merely to make it finish;
- replacing a documented dataset/model with a different one;
- using mutation outcome information to guide restoration;
- selecting fixes because they appear more likely to produce KILLED or
  SURVIVED;
- substituting CPU for a workflow that genuinely requires CUDA or other
  specialized hardware;
- constraining the TARGET dependency in a dependency-pin case in a way that
  cancels or weakens the frozen package==version -> package>=version mutation.

### Reproducible baseline freeze

A first successful baseline is not yet sufficient to freeze the restoration
recipe.

The tentative restoration recipe must be applied to a fresh independent
baseline environment.

If that fresh environment also satisfies the frozen baseline oracle and reaches
the required frozen target, the restoration recipe becomes frozen for that
case.

The frozen recipe must record, as applicable:

- interpreter/runtime;
- package channels and indexes;
- dependency constraints;
- installed package versions;
- build prerequisites;
- environment variables;
- public external artifact provenance.

If fresh reproduction exposes a new substantive compatibility failure, further
error-directed corrections may be made only within the remaining eight-
correction budget.

### Baseline/mutant symmetry

After the restoration recipe is frozen, baseline and mutant evaluation must use
fresh independent environments provisioned from the same frozen recipe.

All compatibility adaptations must be symmetric.

The exact frozen mutation must be the only intended baseline-versus-mutant
difference.

For dependency-pin cases, the TARGET dependency must retain the frozen
baseline-versus-mutant distinction and may not be constrained by the
restoration recipe in a way that neutralizes the mutation.

### Mutation evaluation and semantic verification

Only after a reproducible valid baseline has been established may the exact
frozen mutation be applied.

The identical frozen validation workflow and oracle are then executed in the
mutant environment.

D026 target-execution requirements remain applicable.

Semantic verification follows the existing operator-specific rules.

Mutation outcomes remain:

- KILLED
- SURVIVED
- EQUIVALENT

Setup/restoration failure remains distinct from mutation outcome.

### D027 restoration classifications

A D027 case may be recorded as:

- restored — a reproducible valid baseline was obtained;
- not-restored — the case exhausted the D027 correction budget or applicable
  D027 stage limit without a valid reproducible baseline;
- workflow-unavailable — restoration established that the frozen workflow
  requires an unavailable external resource/hardware or cannot exercise the
  frozen target;
- infrastructure-invalid — the attempt was invalidated by suspend, DNS,
  transient network failure, broken sandboxing, or equivalent host
  infrastructure failure.

Infrastructure-invalid attempts may be repeated fresh and do not consume a
substantive compatibility correction unless an intentional compatibility
adaptation was also made.

### Reporting and provenance

D027 must never delete or rewrite earlier reports.

D027 reports use separate paths of the form:

    benchmarks/corpus/runs/D027-<case-id>-manual-restoration.json

A D027 report must reference the canonical case and preserve a chronological
record of:

- historical evidence consulted;
- each observed failure;
- each compatibility correction;
- correction count;
- environment recipe;
- baseline reproduction;
- mutation execution if reached;
- semantic verification if reached;
- final D027 restoration classification;
- mutation outcome if evaluated.

D027 results do not replace the canonical screening.jsonl line.

### Execution order

All 24 frozen cases are intended for restoration.

Execution order is not an inclusion criterion.

B02-28 may be used as the first technical D027 case because its canonical
failure provides a concrete historical compatibility problem
(scikit-multiflow / NumPy / historical Python environment), but success or
failure on B02-28 must not affect whether the remaining cohort cases are
attempted.

Status:

FROZEN BEFORE FIRST D027 RESTORATION EXECUTION.

## D028 — End of execution and restoration phase

The empirical execution phase is now closed.

All intended primary repositories were processed:
- B01: 10/10
- B02: 29/29
- total: 39/39

D027 manual restoration was conducted on a subset of initially non-evaluable
cases subject to available research time and resources.

Cases without a D027 restoration report are classified as "D027 not attempted"
and retain their canonical primary classification. They must not be counted as
failed D027 restorations.

No further repository execution or environment restoration will be performed
for the current study dataset.

Canonical primary results remain unchanged. D027 results remain a separate
restoration layer.

Subsequent work is limited to accounting, analysis, figures, manuscript
preparation, and software/package validation.

## D028 — End of execution and restoration phase

The empirical execution and restoration phase is closed at this point.

All intended primary repositories were processed:
- B01: 10/10
- B02: 29/29
- total: 39/39

D027 manual restoration was attempted for a subset of initially non-evaluable
cases under the frozen D027 restoration protocol.

Cases without a D027 restoration report are classified as D027-not-attempted.
They retain their canonical primary classification and must not be counted as
failed D027 restoration attempts.

No further candidate-repository execution or environment restoration will be
performed for the current study dataset.

Canonical primary results remain unchanged. D027 results remain a separate
restoration layer and must not silently overwrite canonical primary outcomes.

Subsequent study work is limited to:
- final accounting;
- statistical analysis;
- figures and tables;
- manuscript preparation;
- MLReproMutate software/package validation.
