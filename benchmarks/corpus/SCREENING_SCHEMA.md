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
