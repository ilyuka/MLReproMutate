# Screening record schema

`screening.jsonl` contains one JSON object per line.

Required top-level fields:

    schema_version
    repository
    revision
    operator
    research
    workflow
    screening
    baseline
    mutation

Example:

    {
      "schema_version": 1,
      "repository": "owner/repository",
      "revision": "40-character commit SHA",
      "operator": "random-seed",
      "research": {
        "kind": "paper",
        "reference": "https://doi.org/..."
      },
      "workflow": {
        "kind": "documented-example",
        "command": "python example.py",
        "reference": "README.md"
      },
      "screening": {
        "status": "eligible",
        "reason": null,
        "compatibility_retry_used": false
      },
      "baseline": {
        "status": "passed",
        "duration_seconds": 2.1
      },
      "mutation": {
        "status": "evaluated",
        "candidate_index": 1,
        "outcome": "survived",
        "report_path": "runs/example.json"
      }
    }

Allowed operators:

    dependency-pin
    random-seed
    data-split
    cv-fold-count

Allowed workflow kinds:

    upstream-test
    documented-validation
    documented-experiment
    documented-example
    ci

Allowed screening statuses:

    eligible
    setup-failed
    no-applicable-mutation
    workflow-unavailable
    out-of-scope

Allowed baseline statuses:

    passed
    failed
    not-run

Allowed mutation statuses:

    evaluated
    not-evaluated

Allowed evaluated outcomes:

    killed
    survived
    invalid
    equivalent
    timeout
    error

## Schema version 2: post-calibration primary corpus

Batch B01 remains schema version 1.

All post-calibration primary corpus records use:

    "schema_version": 2
    "protocol_version": "2.0"

Schema version 2 retains all schema-version-1 fields and adds the following
required metadata.

### Validation oracle

`workflow.oracle_kind` is required and must be one of:

    assertion
    metric-threshold
    reference-comparison
    completion-only

Example:

    "workflow": {
      "kind": "documented-example",
      "oracle_kind": "completion-only",
      "command": "python example.py",
      "reference": "README.md"
    }

### Semantic verification

`mutation.semantic_verification` is required for schema-version-2 records.

Allowed statuses:

    confirmed-non-equivalent
    confirmed-equivalent
    unverified
    not-run

Structure:

    "semantic_verification": {
      "status": "confirmed-non-equivalent",
      "method": "Compared generated split membership for baseline and mutant.",
      "evidence": "Held-out sample membership changed."
    }

`method` and `evidence` must each be a string or null.

For a `survived` mutation, semantic verification must be either
`confirmed-non-equivalent` or `unverified`.

For an `equivalent` mutation, semantic verification must be
`confirmed-equivalent`.

For a mutation that was not evaluated, semantic verification must be
`not-run`.

A schema-version-1 B01 record remains valid without these additional fields.

