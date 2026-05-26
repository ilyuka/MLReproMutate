# Empirical Corpus Protocol

This document defines the repository-screening and mutation-evaluation protocol
used for the MLReproMutate empirical study.

The protocol is fixed before systematic corpus collection begins.

## Research question

For realistic reproducibility-relevant mutations introduced into machine
learning research software, do the repository's existing validation safeguards
detect the change?

A safeguard may be an upstream test, CI validation command, documented example,
or documented experiment workflow.

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
2. documented repository validation or experiment command;
3. documented example or quickstart exercising the target;
4. repository CI command that can be reproduced locally.

A workflow created specifically by MLReproMutate is not accepted as corpus
evidence about the strength of an upstream repository safeguard.

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

Whenever practical, all candidates exercised by the selected workflow are
evaluated independently.

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

A surviving mutation should receive semantic verification whenever feasible.

Examples:

- dependency mutation: verify that dependency resolution actually changed;
- seed mutation: verify that the generated random partition/order changed;
- data-split mutation: compare sample membership or class distribution;
- CV-fold mutation: verify that the executed number of folds changed.

Observable metric changes may provide additional evidence but are not required
when the mutated research policy itself is demonstrably different.

## Resource budget

The default validation timeout is 300 seconds per baseline or mutant unless a
repository-specific value is declared before observing the mutation outcome.

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

