---
title: "MLReproMutate: Mutation Testing for Reproducibility Safeguards in Machine-Learning Research Software"
date: 29 August 2026
tags:
  - Python
  - mutation testing
  - reproducibility
  - machine learning
  - research software
authors:
  - name: Ilya Shulepov
    orcid: 0009-0001-1348-9576
    affiliation: 1
affiliations:
  - name: Independent Researcher
    index: 1
bibliography: paper.bib
---

# Summary

MLReproMutate is Python research software for mutation testing of
reproducibility-relevant safeguards in machine-learning research software.
It introduces controlled changes to experimental and environment choices and
evaluates whether validation workflows already present in a repository detect
those changes.

The software currently implements mutation operators for random seeds,
dependency constraints, data-split stratification, and cross-validation fold
counts. Rather than mutating learned model parameters or generating adversarial
inputs, MLReproMutate targets choices encoded in the surrounding experimental
software and configuration. Each mutation is evaluated relative to an
executable unmodified baseline. The default sandbox execution mode evaluates
mutations in isolated temporary project copies, while an explicit in-place mode
is available for disposable or otherwise safely resettable workspaces.

MLReproMutate is intended for researchers studying research-software quality,
machine-learning reproducibility, and mutation testing, as well as developers
who want to evaluate whether their existing validation workflows are sensitive
to reproducibility-relevant configuration changes.

# Statement of need

Machine-learning results can depend on choices such as random seeds, dependency
versions, data partitioning, and evaluation protocols. Prior work has shown
that such choices can affect measured performance and that research-code
availability alone does not guarantee reproducibility
[@reimers2017score; @bouthillier2021variance; @trisovic2022execution].

A repository may nevertheless contain tests, continuous integration,
validation scripts, examples, or executable experiments that run successfully
without checking these choices explicitly. Ordinary successful execution
therefore does not reveal whether an existing validation workflow would detect
a scientifically relevant change in experimental configuration.

Mutation testing provides a way to make this counterfactual observable:
introduce a controlled change and determine whether the available validation
mechanism distinguishes the mutant from the original program
[@jia2011mutation]. MLReproMutate applies this principle specifically to
reproducibility-relevant choices in machine-learning research software.

The target users are empirical software-engineering researchers studying
research-code validation, machine-learning researchers assessing safeguards in
their experimental repositories, and developers of research software who want
to test whether validation workflows constrain important experimental choices.

# State of the field

General-purpose Python mutation-testing systems such as Cosmic Ray and mutmut
modify program source code and execute tests to assess test-suite effectiveness
[@cosmicray; @mutmut]. These tools provide mature implementations of
conventional mutation testing, but their mutation models are primarily
program-behavior oriented rather than representations of specific
reproducibility choices in machine-learning experiments.

Mutation testing has also been adapted specifically to machine-learning
systems. DeepMutation introduced source- and model-level mutation operators for
deep-learning systems, while DeepCrime developed operators based on observed
deep-learning faults [@ma2018deepmutation; @humbatova2021deepcrime]. These
approaches primarily use mutation to evaluate model test data or other
deep-learning testing mechanisms.

MLReproMutate addresses a different measurement target: whether validation
workflows already present in a research repository detect controlled changes
to reproducibility-relevant experimental choices. Its operators therefore
represent concepts such as an explicit random seed, an exact dependency pin,
stratified data splitting, or a cross-validation fold count.

Extending a general-purpose mutation engine was considered conceptually less
appropriate because the research protocol requires more than source rewriting.
MLReproMutate separates candidate detection from mutation application, retains
metadata identifying the selected experimental choice, executes an unmodified
baseline before interpreting mutation outcomes, isolates each mutation in a
separate workspace, and supports semantic verification for dependency
mutations. In particular, relaxing `package==version` to `package>=version`
does not by itself demonstrate that the resolved environment changed; resolved
dependency evaluation therefore compares the installed target versions before
interpreting a mutation outcome. These abstractions are central to the research
question rather than extensions of conventional syntax-level mutation
operators.

# Software design

MLReproMutate represents mutation testing as three separable concerns:
candidate identification, controlled mutation, and validation execution.

Operators first detect syntactically supported mutation candidates. Python
source operators use abstract-syntax-tree information and record source
locations and operator-specific metadata. Mutation application then acts on a
previously selected candidate and verifies that the expected target is still
present before rewriting it. This separation permits candidate selection to be
performed independently of mutation execution and supports empirical protocols
in which targets are fixed before outcomes are observed.

The current release implements four mutation classes. `random-seed` increments
a supported literal seed by one. `dependency-pin` relaxes an exact dependency
constraint from `package==version` to `package>=version`. `data-split` replaces
an explicit non-`None` `stratify` argument in a supported
`train_test_split` call with `None`. `cv-fold-count` increments an explicit
cross-validation `n_splits` value by one.

Evaluation is baseline-first. The selected validation command is run against
the unmodified project before mutants are interpreted. A baseline failure or
timeout is therefore kept separate from a mutation result. After a successful
baseline, each mutation is evaluated using the same validation command. The
default sandbox mode uses an isolated temporary project copy; the optional
in-place mode restores the mutation target after evaluation. Successful
validation corresponds to a survived mutation, while a non-zero validation
exit status corresponds to a killed mutation; other execution states are
represented separately.

This design deliberately does not treat mutation survival as evidence that a
repository is irreproducible. A surviving mutation establishes only that the
selected validation workflow did not detect that particular controlled change.

# Research impact statement

MLReproMutate has already been used as the experimental instrument in an
outcome-blind empirical study of reproducibility safeguards in real
machine-learning research repositories [@shulepov2026empirical]. The study
evaluated 39 frozen repository--operator cases across four
reproducibility-relevant mutation classes. It used frozen repository
revisions, mutation candidates, and validation workflows and explicitly
separated baseline executability, semantic equivalence, and mutation outcomes.

The study and accompanying machine-readable artifacts provide a reproducible
reference application of the software rather than a hypothetical future use
case. The study used MLReproMutate version 0.1.0 and its frozen archived
artifacts [@mlrepromutate2026empirical]. The current public software release,
version 0.1.2, is archived separately as a newer version on Zenodo
[@mlrepromutate2026current].

The project also provides automated tests, continuous integration across
supported Python versions, worked examples, contribution guidelines, and a
public issue tracker to support reuse and external evaluation.

# AI usage disclosure

OpenAI ChatGPT and OpenAI Codex were used from February 2026 through
August 2026 during software development, documentation preparation, research
workflow assistance, and manuscript drafting. In both products, the author
used the latest model version available at the time of use rather than pinning
the project to a single fixed model. Consequently, the specific model changed
as OpenAI released newer versions during the project period. The models used
across this period were from the GPT-5 family, including GPT-5.3-Codex and
GPT-5.4 during earlier development and GPT-5.6 Sol during the final preparation
stage.

ChatGPT was used for discussion of software and empirical-study design, code
and documentation review, drafting and editing assistance, and analysis of
research materials. Codex was used for selected repository-analysis,
code-development, testing, and software-maintenance workflows.

All AI-assisted outputs included in the software, documentation, empirical
materials, and manuscript were reviewed and validated by the author. The
author made the research-design decisions, selected and froze the empirical
protocol, determined the interpretation of study outcomes, made the core
software-design decisions, and remains responsible for the accuracy,
originality, licensing, and scientific claims of the submitted work.

# Acknowledgements

No external financial support was received for this work.

# References