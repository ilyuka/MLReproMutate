# RQ2 workflow/oracle analysis codebook

Status: post-freeze analysis protocol

This file defines the RQ2 analysis variables and blinding rules for the frozen
MLReproMutate empirical study. It does not alter the empirical corpus, mutation
operators, selected candidates, selected workflows, outcomes, restoration
protocol, or the `empirical-results-freeze` checkpoint.

## Research question

RQ2: How does mutation detection differ by validation-workflow type and by the
strength of the workflow's validation oracle?

## Source-of-truth hierarchy

The RQ2 analysis must preserve the classifications and terminology that were
already fixed in the empirical protocol wherever they exist.

Primary sources are:

1. `benchmarks/corpus/PROTOCOL.md`;
2. `benchmarks/corpus/SCREENING_SCHEMA.md`;
3. `benchmarks/corpus/sampling_frame.jsonl` for prospective B02 workflow/oracle metadata;
4. `benchmarks/corpus/screening.jsonl` for frozen selected workflow metadata;
5. frozen upstream source/documentation at the selected revision only when a
   schema-v1 B01 oracle must be classified retrospectively.

Mutation outcomes, semantic-verification outcomes, restoration success, mutant
return codes, and post-mutation observations must not be used to assign or
revise an oracle classification.

## Important protocol fact

Protocol version 2 already prospectively defined both the RQ2 workflow variable
and the validation-oracle categories. Every selected B02 workflow received an
`oracle_kind` before mutation execution.

Therefore RQ2 must not replace this prospective classification with a new
post-hoc O1/O2/O3/O4 strength scale.

## Unit of coding

The evidence frame contains all 39 frozen repository/operator cases:

- B01 calibration: 10 cases;
- B02 primary frame: 29 cases.

The evidence frame is constructed without mutation outcomes.

The analytic denominator is applied only after the classification/evidence
frame is frozen.

## Primary variable 1: validation workflow kind

Use the frozen `workflow.kind` / `workflow_kind` value exactly as recorded.
Allowed protocol values are:

- `upstream-test`;
- `ci`;
- `documented-validation`;
- `documented-experiment`;
- `documented-example`.

Workflow kind is categorical. Do not impose an ordinal interpretation such as
"example < experiment < test".

## Primary variable 2: validation oracle kind

For schema-version-2 B02 cases, preserve the prospectively recorded
`oracle_kind` exactly:

- `assertion`: explicit assertions or test expectations determine success;
- `metric-threshold`: an explicit numerical acceptance threshold determines success;
- `reference-comparison`: output is compared with an expected/reference artifact or value;
- `completion-only`: success means only that the workflow completed with exit status zero.

Do not infer oracle kind from whether the mutation was killed or survived.

In the frozen B02 sampling frame, only `assertion` and `completion-only` are
observed. The unused allowed categories remain part of the protocol vocabulary
but must not be populated artificially.

## Derived oracle contrast

For a compact descriptive strength contrast, define before joining outcomes:

- `completion-only` -> `completion-only`;
- `assertion`, `metric-threshold`, `reference-comparison` -> `substantive-oracle`.

This is a derived binary descriptor, not a claim that all substantive oracles
have equal strength. No additional ordering among the substantive categories is
assumed.

## B01 calibration handling

B01 remains schema version 1 and must not be rewritten to appear prospectively
collected under protocol version 2. Its records therefore do not contain the
prospective `oracle_kind` field.

Consequences:

1. workflow-kind analyses may use the frozen B01 `workflow.kind` values;
2. the primary prospective oracle-kind analysis should use B02;
3. any B01 oracle coding must be labelled `retrospective-blinded`;
4. B01 oracle classification must use only frozen workflow/source evidence and
   never mutation outcome, semantic verification, restoration outcome, or mutant output.

## Restoration handling

D027 is an executability/restoration layer and does not define a new validation
workflow or oracle. A successfully restored case retains its frozen selected
workflow and oracle metadata.

Restoration status is joined only after the RQ2 evidence/classification frame is
frozen.

## Outcome blinding

The RQ2 evidence sheet excludes:

- mutation outcome;
- mutation evaluation status;
- semantic-verification status/evidence;
- baseline pass/fail result;
- screening failure reason containing execution-result information;
- restoration outcome/status;
- mutant return code;
- any textual KILLED/SURVIVED/EQUIVALENT/non-evaluable statement.

Repository identity, fixed revision, selected workflow command/reference, and
prospectively recorded B02 oracle kind are not outcomes and may remain.

## Classification freeze

Before any outcome-based RQ2 table is generated:

1. construct the 39-case outcome-stripped evidence frame;
2. verify all B02 `oracle_kind` values against the frozen sampling frame;
3. leave B01 `oracle_kind` missing until a separate retrospective-blinded review;
4. freeze the evidence/classification artifact;
5. only then join empirical evaluability, semantic status, and mutation outcome.

No category may be changed after the outcome join because the resulting pattern
appears inconvenient or explanatory.

## Planned primary RQ2 analyses

### RQ2a: workflow kind

Among confirmed non-equivalent evaluated mutations, report by workflow kind:

- number evaluated;
- KILLED;
- SURVIVED;
- descriptive detection proportion.

### RQ2b: prospectively recorded oracle kind

Use B02 cases with prospectively recorded oracle metadata and report the same
counts by `oracle_kind`.

### RQ2c: derived oracle contrast

Report `completion-only` versus `substantive-oracle` as a compact descriptive
contrast. Do not claim causal superiority or statistical significance by default.

### Optional B01 sensitivity analysis

Only after a separate retrospective-blinded B01 source classification is frozen,
a combined B01+B02 oracle table may be reported as sensitivity/exploratory
evidence.

## Statistical interpretation

RQ2 is primarily descriptive/exploratory because detected mutations and
category cell sizes are small and uneven.

Do not infer general superiority or causality from category differences.
