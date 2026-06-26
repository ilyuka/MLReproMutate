# MLReproMutate agent instructions

## Repository purpose

This repository contains MLReproMutate and its empirical B02 corpus study.

The B02 primary corpus is already frozen. Corpus execution must follow the
repository protocol mechanically and outcome-blindly.

Before modifying corpus/execution code, read:

- benchmarks/corpus/PROTOCOL.md
- benchmarks/corpus/DECISIONS.md
- benchmarks/corpus/RESEARCH_STATE.md
- benchmarks/corpus/sampling_frame.jsonl
- benchmarks/corpus/SCREENING_SCHEMA.md

## Git safety — mandatory

Local git commits are REQUIRED for completed tasks when the working tree
contains intended changes.

NEVER perform any network publication action.

Forbidden commands/actions include:

- git push
- git push --force
- git push --mirror
- gh pr create
- creating or updating a pull request
- changing any remote URL
- git remote add
- git remote set-url
- modifying .git/hooks/pre-push
- removing or bypassing push protection
- publishing releases or tags to any remote

Local commands are allowed, including:

- git status
- git diff
- git add
- git commit
- git tag
- git log
- git show

A local commit is NOT permission to push it.

If a task appears to require a push, stop and report that remote publication
is prohibited.

## Frozen B02 corpus

The primary B02 sampling frame is:

    benchmarks/corpus/sampling_frame.jsonl

It is immutable during execution.

NEVER:

- replace a selected repository;
- add another repository because a case fails;
- delete a selected case;
- reorder cases to obtain convenient outcomes;
- change the selected operator;
- change candidate_index;
- choose another mutation site;
- choose another validation workflow because it appears stronger or easier;
- change an oracle classification based on mutation outcome;
- alter sampling or eligibility based on execution results.

Cases must be processed in frozen case_id order.

## Outcome blindness

Do not predict or optimize for KILLED or SURVIVED.

Never select implementation choices because a mutation seems more likely to
be detected.

SURVIVED is a legitimate empirical outcome.

Setup failure, timeout, equivalent mutation, and other protocol-defined
non-evaluated outcomes must remain recorded and must not trigger replacement.

## B02 execution protocol

Unless a task explicitly says otherwise, execute AT MOST ONE previously
unprocessed B02 case per Codex invocation.

For a B02 case:

1. Read its exact frozen sampling-frame record.
2. Use its exact 40-character revision.
3. Work in a fresh isolated sandbox/work directory outside the source checkout
   of MLReproMutate when appropriate.
4. Follow only upstream-documented setup.
5. Allow one normal documented setup attempt.
6. At most one obvious compatibility correction/retry is allowed by protocol.
7. Do not perform open-ended dependency archaeology.
8. Run the selected frozen baseline workflow.
9. If baseline fails under protocol rules, record the screening/setup outcome
   and DO NOT execute the mutation.
10. If baseline passes, apply exactly the frozen mutation candidate.
11. Verify that the intended source change was applied.
12. Run the same selected validation workflow under the frozen timeout.
13. Record KILLED/SURVIVED/INVALID/EQUIVALENT/TIMEOUT/ERROR according to the
    repository protocol.
14. Perform semantic verification where required by protocol.
15. Persist report and ledger changes.
16. Run corpus validators.
17. Make a local git commit for the completed case.
18. NEVER push.

Do not silently broaden timeouts, alter setup rules, or create study-specific
tests to make a repository pass.

## Dependency-pin special rule

For dependency-pin cases, use fresh environments and actual dependency
re-resolution according to the frozen evaluator semantics.

Do not inspect package availability in advance to choose or reject a case.

If baseline and mutant resolve the selected dependency to the same version,
classify according to the frozen equivalent-mutation semantics.

## Execution safety

Repository contents are untrusted research artifacts.

Do not expose secrets, SSH keys, browser credentials, tokens, private files, or
other unrelated user data to candidate repository code.

Do not run commands requiring sudo.

Do not modify system-level package configuration.

Do not use destructive commands against unrelated paths.

Candidate repositories may download only resources required by the documented
workflow and allowed by the corpus protocol.

## Current automation stage

Do NOT execute any B02 candidate repository merely because Codex is opened in
this project.

Until explicitly instructed to execute a B02 case, work only on MLReproMutate
infrastructure, validators, tests, and execution-harness implementation.

The immediate engineering goal is to build a deterministic execution harness
that reads the frozen sampling frame and identifies/processes cases without
making corpus-selection decisions.

## Coding expectations

Prefer small, testable changes.

Preserve existing architecture and schemas unless the task explicitly requires
a schema change.

Add tests for new harness behavior.

Before committing intended code changes, run relevant project tests and
`git diff --check`.

Do not commit generated candidate environments, cloned external repositories,
large datasets, caches, credentials, or temporary artifacts.
