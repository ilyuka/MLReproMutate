# MLReproMutate Threat Model

## 1. Purpose

MLReproMutate is designed to evaluate whether the safeguards surrounding a
machine-learning experiment detect changes that threaten experimental
reproducibility.

The software intentionally introduces controlled reproducibility faults and
observes the response of existing validation mechanisms such as tests,
configuration validation, CI checks, and experiment-level assertions.

## 2. Research question

The primary question is:

> If a realistic reproducibility fault is introduced into a machine-learning
> experiment, do the project's existing safeguards detect it?

## 3. Scope

The initial scope is CPU-runnable Python machine-learning research software.

Initial mutation categories are:

1. dependency specification;
2. dataset or artifact identity;
3. experiment configuration;
4. preprocessing;
5. random state;
6. artifact provenance.

## 4. Non-goals

MLReproMutate is not intended to provide:

- adversarial ML testing;
- neural-network architecture mutation;
- neuron-level mutation;
- robustness evaluation;
- model-quality evaluation;
- generic source-code mutation testing;
- experiment tracking;
- MLOps orchestration.

## 5. Mutation outcome definitions

### KILLED

At the execution level, a mutation is `KILLED` when the selected validation
workflow returns a non-zero status after the mutation is applied.

### SURVIVED

At the execution level, a mutation is `SURVIVED` when the selected validation
workflow completes successfully after the mutation is applied.

A survived mutation does not prove that the repository or its scientific
results are irreproducible. It means only that the selected validation workflow
did not detect that controlled change.

### INVALID

A mutation is `INVALID` when the generated modification does not represent a
valid instance of the intended reproducibility fault or makes the experiment
unusable for unrelated reasons.

### EQUIVALENT

A mutation is `EQUIVALENT` when the mutation is applied successfully but does
not change the relevant reproducibility property.

### TIMEOUT

The validation run exceeded the configured execution time.

### ERROR

The experiment could not be evaluated because of an infrastructure or
framework error unrelated to the intended mutation.

## 6. Initial mutation categories

### Dependency mutations

Examples:

- replace an exact dependency pin with a version range;
- remove a reproducibility-critical version constraint.

### Dataset and artifact identity

Examples:

- remove a content checksum;
- replace a pinned dataset revision with a mutable reference.

### Configuration

Examples:

- change a research-relevant parameter without updating tracked experiment
  configuration.

### Preprocessing

Examples:

- alter a tracked preprocessing parameter.

### Randomness

Examples:

- remove an explicit random seed;
- modify a reproducibility-critical random-state configuration.

### Artifact provenance

Examples:

- remove an artifact version or hash required to identify the exact model,
  dataset, or intermediate result.

## 7. Open research questions

Important unresolved questions include:

- How should equivalent reproducibility mutants be identified?
- Which mutation categories are applicable across different ML frameworks?
- What safeguards should count as valid mutation detectors?
- How should stochastic output differences be interpreted?
- How should infrastructure failures be separated from killed mutations?

These questions will be refined through experiments on real ML repositories.
