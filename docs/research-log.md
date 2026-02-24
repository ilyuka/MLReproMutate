# Research Log

This log records experimental observations and design decisions made during
the development and evaluation of MLReproMutate.

---

## 2026-02 — Project initialization

### Goal

Establish the initial public project structure and formalize the research
problem before implementing mutation operators.

### Current hypothesis

Existing tests and CI pipelines in ML research repositories may fail to detect
changes that compromise experimental reproducibility.

### Initial mutation classes

- dependencies;
- dataset/artifact identity;
- configuration;
- preprocessing;
- randomness;
- artifact provenance.

### Current uncertainties

- How frequently will real repositories contain applicable mutation targets?
- How often will mutations be invalid or equivalent?
- Which repository safeguards should count as mutation detectors?
- Can the approach produce useful findings without expensive model training?

### Next experiment

Implement one deterministic dependency-related mutation and evaluate it on a
small CPU-runnable ML example.