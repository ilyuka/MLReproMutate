# Related Tools and Research Context

This page positions MLReproMutate against the closest tool classes. It is a
concise guide rather than a systematic literature review; the project
[paper](../paper/paper.md) and [bibliography](../paper/paper.bib) are the
authoritative project-local sources for the claims below.

## 1. Conventional mutation testing

[Cosmic Ray](https://cosmic-ray.readthedocs.io/) and
[mutmut](https://github.com/boxed/mutmut) are general-purpose Python mutation
testing tools. They modify program source and run tests or another validation
command to determine whether the introduced behavioral change is detected.
They are appropriate references for conventional mutation testing, in which
mutants are used to assess validation or test-suite effectiveness.

MLReproMutate is not presented as a replacement for these tools. It uses the
general mutation-testing principle but defines a domain-specific mutation model
and a different measurement target.

## 2. Mutation testing for ML systems

[DeepMutation](https://doi.org/10.1109/ISSRE.2018.00021) introduced source- and
model-level mutations for deep-learning systems and used mutant detection in
part to assess test-data quality. [DeepCrime](https://doi.org/10.1145/3460319.3464825)
derives deep-learning-specific source-level mutation operators from real fault
evidence and uses them to assess deep-learning test data.

These approaches establish prior use of domain-specific mutation testing for
ML systems. Their principal measurement targets differ from MLReproMutate's:
MLReproMutate evaluates an existing repository validation workflow against
controlled changes to reproducibility-relevant experimental choices, rather
than primarily evaluating model test data or trained-model robustness.

## 3. Reproducibility tooling

Environment capture, experiment tracking, provenance recording, and data or
artifact versioning address complementary reproducibility problems. They help
record, reconstruct, or manage an experiment and its inputs. MLReproMutate asks
a narrower mutation-testing question: whether a validation workflow already
present in a repository detects a deliberately introduced change. It does not
replace those reproducibility tools, and they do not by themselves answer this
measurement question.

## 4. Position of MLReproMutate

MLReproMutate currently mutates four kinds of reproducibility-relevant choice:
random seeds, dependency constraints, data-split stratification, and
cross-validation fold counts. A `KILLED` result means the selected validation
workflow returned a non-zero status after the mutation; a `SURVIVED` result
means it completed successfully. Survival shows only that this workflow did not
detect this controlled change; it is not proof that the repository or its
scientific results are irreproducible.

The separate package reflects this mutation model and evaluation target. Its
research protocol requires baseline-first evaluation, separation of candidate
detection from mutation application, isolated workspace execution,
machine-readable result and provenance reporting, and explicit treatment of
semantic equivalence where needed. For example, a relaxed dependency constraint
may resolve to the same installed version, so resolved dependency evaluation
checks the installed target version before interpreting the outcome. These
abstractions complement conventional mutation-testing engines rather than
reimplementing only their syntax-level source mutations.
