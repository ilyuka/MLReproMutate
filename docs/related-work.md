# Related Work Notes

This file contains working notes for the related-work analysis of
MLReproMutate.

It is not intended to be a finished literature review.

## 1. Conventional mutation testing

Questions:

- What does conventional mutation testing evaluate?
- Which mature Python mutation-testing tools exist?
- How are killed, survived, and equivalent mutants defined?

Known tools / papers:

### Cosmic Ray

URL:
TODO

Main purpose:
TODO

Relationship to MLReproMutate:
TODO

### mutmut

URL:
TODO

Main purpose:
TODO

Relationship to MLReproMutate:
TODO

---

## 2. Mutation testing for machine learning

Questions:

- What kinds of ML artifacts are mutated?
- Is the target model robustness, test-data quality, software testing, or
  experiment reproducibility?

### DeepMutation

Paper:
TODO

Main contribution:
TODO

Difference from MLReproMutate:
TODO

---

## 3. ML reproducibility

Topics:

- dependency drift;
- random seeds;
- dataset versioning;
- preprocessing;
- environment capture;
- artifact provenance.

Papers:
TODO

---

## 4. Experiment tracking and provenance tools

Candidate systems:

- MLflow
- DVC
- DataLad
- ReproZip
- other relevant tools

For each tool record:

- exact research/software purpose;
- what reproducibility information it captures;
- whether it actively tests safeguards;
- relationship to MLReproMutate.

---

## 5. Scientific workflow testing

TODO

---

## 6. Build-vs-contribute analysis

For every close alternative, answer:

1. Could MLReproMutate functionality reasonably be added to this project?
2. Would doing so preserve the intended research question?
3. What domain-specific concepts would still be missing?
4. Why is a separate project justified, if it is?

---

## Search log

### 2026-02

Queries:
TODO

Sources checked:
TODO

Findings:
TODO