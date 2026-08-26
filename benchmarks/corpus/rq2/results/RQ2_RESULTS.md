# RQ2 descriptive results

## Denominators

Combined confirmed non-equivalent evaluated mutations:

- N = 23
- KILLED = 2
- SURVIVED = 21

B02 confirmed non-equivalent evaluated mutations with prospective
oracle metadata:

- N = 15
- KILLED = 2
- SURVIVED = 13

## RQ2a — Detection by frozen workflow kind

| Workflow kind | Confirmed non-equivalent evaluated | KILLED | SURVIVED | Detection |
|---|---:|---:|---:|---:|
| upstream-test | 6 | 0 | 6 | 0.0% |
| ci | 1 | 0 | 1 | 0.0% |
| documented-validation | 2 | 1 | 1 | 50.0% |
| documented-experiment | 3 | 0 | 3 | 0.0% |
| documented-example | 11 | 1 | 10 | 9.1% |

Workflow kind is categorical; no ordinal ranking is assumed.

## RQ2b — B02 detection by prospectively recorded oracle kind

| Oracle kind | Confirmed non-equivalent evaluated | KILLED | SURVIVED | Detection |
|---|---:|---:|---:|---:|
| assertion | 2 | 0 | 2 | 0.0% |
| metric-threshold | 0 | 0 | 0 | — |
| reference-comparison | 0 | 0 | 0 | — |
| completion-only | 13 | 2 | 11 | 15.4% |

B01 is excluded from this primary oracle-kind analysis because
schema-v1 B01 did not prospectively record `oracle_kind`.

## RQ2c — B02 derived oracle contrast

| Oracle contrast | Confirmed non-equivalent evaluated | KILLED | SURVIVED | Detection |
|---|---:|---:|---:|---:|
| substantive-oracle | 2 | 0 | 2 | 0.0% |
| completion-only | 13 | 2 | 11 | 15.4% |

The binary contrast was frozen before outcome join:
`completion-only` versus `substantive-oracle`.

## Interpretation constraint

These are descriptive results from a small and uneven sample with
only two detected confirmed non-equivalent mutations.

They do not establish causal effects, population-wide differences,
or statistical superiority of one workflow/oracle category.
