# Empirical Corpus Protocol

This document defines the repository-screening and mutation-evaluation protocol
used for the MLReproMutate empirical study.

The protocol is fixed before systematic corpus collection begins.

## Research questions

RQ1: When realistic reproducibility-relevant mutations are introduced into
machine-learning research software, how often are they detected by existing
repository validation workflows?

RQ2: How does mutation detection differ by validation-workflow type and by the
strength of the workflow's validation oracle?

A validation workflow may be an upstream test, reproducible CI command,
documented validation command, documented experiment, or documented example.

The term `validation workflow` is intentionally broader than `safeguard`.
A workflow that only completes successfully, without assertions, thresholds, or
reference comparisons, is not assumed to be a strong reproducibility safeguard.

## Mutation classes

The primary mutation set is frozen to four fault classes:

1. Dependency specification

       package==version
           ->
       package>=version

2. Randomness

       explicit seed N
           ->
       seed N + 1

3. Data splitting

       train_test_split(..., stratify=value)
           ->
       train_test_split(..., stratify=None)

4. Evaluation protocol

       KFold/StratifiedKFold(..., n_splits=N)
           ->
       n_splits=N + 1

No additional primary mutation class is added after corpus collection starts
without creating a new protocol version.

## Unit of screening

A screening record corresponds to one repository/operator pair at one fixed
repository revision.

A repository may therefore contribute records for multiple operators if more
than one operator is applicable.

## Repository inclusion criteria

A repository is eligible when all of the following hold:

- it is a public GitHub repository;
- it contains machine-learning or closely related research software;
- its research context is identifiable from a paper, DOI, publication,
  research artifact, or explicit research-software documentation;
- the repository is evaluated at a fixed commit SHA;
- the selected MLReproMutate operator has at least one applicable mutation;
- an existing upstream validation workflow can be identified;
- the workflow can be executed non-interactively in the study environment;
- a valid unmutated baseline completes successfully.

## Validation workflow hierarchy

Prefer validation workflows in the following order:

1. existing upstream tests directly exercising the target;
2. repository CI commands that can be reproduced locally and exercise the target;
3. documented repository validation commands;
4. documented experiments exercising the target;
5. documented examples or quickstarts exercising the target.

The selected workflow must exercise the mutation target under the baseline path.

## Validation-oracle classification

Each schema-version-2 corpus record classifies the selected workflow's oracle as
exactly one of:

- `assertion`: explicit assertions or test expectations determine success;
- `metric-threshold`: an explicit numerical acceptance threshold determines
  success;
- `reference-comparison`: output is compared against an expected/reference
  artifact or value;
- `completion-only`: success means only that the workflow completed with exit
  status zero.

This classification is recorded before observing the mutation outcome.

A workflow created specifically by MLReproMutate is not accepted as corpus
evidence about the strength of an upstream repository validation workflow.

Such a workflow may still be used for operator-development or semantic pilots,
but those runs are recorded separately from the empirical corpus.

## Baseline-first rule

No mutation outcome is evaluated unless the unmodified fixed revision first
passes the selected validation workflow.

A failed baseline is a screening exclusion, not a mutation result.

Examples include:

- dependency drift;
- missing undocumented system dependency;
- unavailable external service;
- unavailable required data;
- incompatible runtime;
- interactive workflow;
- timeout.

## Setup rule

Follow the repository's documented setup instructions.

One obvious environment-level compatibility correction is permitted when the
initial setup fails because of ecosystem drift.

Examples:

- selecting the Python version explicitly documented by the repository;
- correcting one clearly identifiable dependency compatibility conflict.

The correction must not modify repository source code or research logic.

After one compatibility correction, another independent setup failure ends
screening for that repository/operator pair.

No extended manual archaeology is performed to force a repository to run.

## Candidate-selection rule

All mutation candidates are detected before mutation evaluation.

If multiple candidates occur in the selected target file, candidate selection
must be based on the baseline workflow's executed code path, not on mutation
outcomes.

`--candidate-index` may be used only to isolate independently evaluated
candidates.

Candidates known not to execute under the selected workflow are not interpreted
as survived mutations.

Exactly one primary candidate is evaluated for each repository/operator
screening case.

When multiple applicable candidates exist, the primary candidate is the first
candidate in the operator's deterministic detection order that is known, from
the baseline code path, to be executed by the selected workflow.

Candidate selection is completed before observing any mutation outcome.

Additional candidates may be evaluated separately as exploratory evidence, but
they are not included in the primary repository/operator detection-rate
denominator.

## Mutation isolation

Each candidate is evaluated independently in a fresh project sandbox.

Only one controlled mutation is introduced per evaluation.

## Outcome semantics

### KILLED

The selected upstream validation workflow returns a non-zero result because of
the mutation.

### SURVIVED

The selected upstream validation workflow completes successfully despite the
mutation.

`SURVIVED` does not mean that the repository is defective or irreproducible.
It means only that the selected workflow did not reject that controlled change.

### INVALID

The mutation could not be meaningfully evaluated because the generated mutant
was invalid or the operator was not applicable as expected.

### EQUIVALENT

The mutation was applied but semantic verification shows that it did not change
the relevant behavior under the selected workload.

### TIMEOUT

The mutant exceeded the pre-declared validation timeout.

### ERROR

Infrastructure or evaluation failed for a reason that cannot be interpreted as
the repository detecting the mutation.

## Non-equivalence verification

A surviving primary mutation must receive semantic verification whenever the
relevant behavior can be observed without creating a new upstream validation
oracle.

Schema-version-2 records distinguish:

- `confirmed-non-equivalent`: verification demonstrates that the relevant
  mutated behavior changed;
- `unverified`: the workflow survived, but non-equivalence could not be
  established with the available post-hoc evidence.

An unverified survivor remains a reported `SURVIVED` outcome, but is excluded
from the primary confirmed mutation-detection denominator.

Examples:

- dependency mutation: verify that dependency resolution actually changed;
- seed mutation: verify that the generated random partition/order changed;
- data-split mutation: compare sample membership or class distribution;
- CV-fold mutation: verify that the executed number of folds changed.

Observable metric changes may provide additional evidence but are not required
when the mutated research policy itself is demonstrably different.

## Primary analysis denominators

Screening feasibility and mutation detection are reported separately.

Screening feasibility:

    eligible evaluated cases / all screened repository-operator cases

Primary confirmed mutation-detection rate:

    KILLED /
    (KILLED + confirmed-non-equivalent SURVIVED)

`setup-failed`, `no-applicable-mutation`, `workflow-unavailable`,
`out-of-scope`, `INVALID`, `TIMEOUT`, `ERROR`, and unverified survivors are
reported separately and do not enter the primary confirmed detection-rate
denominator.

Results are also stratified by mutation operator, workflow kind, and
validation-oracle kind.

## Calibration transition

Batch B01 is the protocol-calibration batch.

Its pre-revision state is preserved by the annotated Git tag
`corpus-b01-calibration`.

B01 records remain schema version 1 and are not rewritten to make them appear
prospectively collected under protocol version 2.

All new primary corpus observations collected after this protocol revision use
schema version 2 and protocol version `2.0`.

The four primary mutation classes, the baseline-first rule, the fixed-SHA rule,
and the one-compatibility-correction rule remain unchanged after calibration.
The B02 stage-specific timeout amendment below supersedes the original common
300-second B02 bound prospectively from B02-03 onward and for the required
B02-01 amended-policy rerun.

No new primary mutation class is introduced during the main corpus because of
observed kill/survival outcomes.

## B02 prospective stage-specific timeout amendment

Adopted on 2026-08-24 after B02-02 and before any B02-03 execution, the B02
resource ceilings are:

    dependency/setup/install:          900 seconds
    clone/checkout/virtualenv creation: 300 seconds
    baseline validation:                300 seconds
    mutant validation:                  300 seconds
    semantic-verification subprocess:   300 seconds

The amendment increases only the dependency/setup/install ceiling. B02-01
demonstrated that the original common 300-second bound can censor dependency
provisioning itself, conflating environment-provisioning cost with validation
execution. The baseline and mutant validation ceilings therefore remain 300
seconds. The one-obvious-compatibility-correction limit is unchanged.

The sampling frame, repositories, revisions, candidates, candidate indices,
workflows, mutation magnitudes, workflow kinds, and oracle kinds are unchanged.
No case is replaced, deleted, or reordered.

The original B02-01 report and ledger record are permanent provenance. Because
that attempt was censored solely by the former setup timeout, B02-01 requires a
fresh isolated rerun under this amended policy before B02-03 is executed. The
rerun must be recorded separately as
`runs/B02-01-amended-policy-rerun.json`; it must not overwrite the original
`runs/B02-01-tslearn-seed.json`. B02-02 is not rerun: its setup completed under
the stricter original ceiling and therefore satisfies the amended ceiling, and
its existing empirical result remains primary.

## Resource budget

The stage-specific B02 ceilings above are declared before the affected
executions and must not be broadened after observing runtime.

Workflows requiring unavailable proprietary data, credentials, interactive
input, or unsupported specialized hardware are excluded rather than manually
rewritten.

## Reporting

Every attempted repository/operator pair receives a screening record,
including exclusions.

Successful mutation evaluations retain the complete MLReproMutate JSON report.

Screening failures remain part of the study denominator and must not be removed
because they are inconvenient or unsuccessful.

## Pilot versus corpus evidence

Development pilots demonstrate operator behavior and real-world applicability.

Corpus evidence additionally requires an existing upstream validation workflow.

The following must therefore remain explicitly distinguishable:

- synthetic fixture;
- real-world semantic/operator pilot;
- empirical corpus evaluation.
