# Changelog

All notable changes to MLReproMutate will be documented in this file.

MLReproMutate is currently pre-1.0 software; its public API may change between
releases.

## [0.1.1] - 2026-08-28

### Fixed

- Report the installed MLReproMutate package version from distribution
  metadata instead of a hard-coded development placeholder.
- Resolve validation commands using either `python` or `python3` when one of
  those common executable aliases is unavailable.

### Added

- Interactive command-line setup for guided project, operator, validation,
  execution-mode, and candidate selection.
- Static `detect` command for previewing mutation candidates without executing
  project code.
- `in-place` execution mode for disposable, CI, container, or otherwise safely
  resettable workspaces.
- Repeatable project-relative `--exclude` options for omitting unnecessary
  paths from sandbox copies.
- User-facing quick-start and command-line documentation.
- CI usage documentation for reproducibility mutation checks.
- Expanded worked examples for the supported mutation operators.
- Public citation and link for the accompanying empirical study,
  arXiv:2608.27100.
- GitHub Actions workflow for PyPI Trusted Publishing.

### Changed

- Require explicit selection of a mutation operator instead of defaulting to
  `dependency-pin`.
- Keep `sandbox` as the safe default execution mode while allowing users to
  avoid full project copies with explicit `in-place` execution.
- Expanded installation, usage, interpretation, isolation, and contribution
  guidance.


## [0.1.0] - 2026-08-27
### Changed

- Reuse a successful baseline validation across all mutation candidates in a single orchestration run.

### Added

- Initial public repository structure.
- Initial project scope and research question.
- Initial threat-model documentation.
- Continuous integration setup.
- Core mutation outcome, candidate, and result models.
- Base interface for reproducibility mutation operators.
- Isolated temporary project sandbox for safe mutation execution.
- Experiment command runner with captured output, exit status, runtime, and timeout handling.
- Dependency mutation operator for relaxing exact pins in requirements files.
- Mutation evaluation pipeline with baseline validation and KILLED, SURVIVED, and TIMEOUT classification.
- End-to-end dependency mutation fixture demonstrating both surviving and killed reproducibility mutations.
- Mutation orchestration layer for detecting and evaluating operator candidates.
- Initial `mlrepromutate run` command for end-to-end dependency mutation evaluation.
- Added incremental CLI progress reporting for baseline validation and individual mutation evaluation.
- Added workflow-aware dependency mutation scoping through `--requirements-file`.
- Mutation progress output now includes the source file and line number.
- Added machine-readable JSON reports containing validation provenance,
  mutation metadata, outcomes, execution durations, and Git revisions.
- Added an isolated virtual-environment resolver foundation for future
  dependency re-resolution experiments.
- Added resolved dependency evaluation with explicit `INVALID`,
  `EQUIVALENT`, `SURVIVED`, `KILLED`, and `TIMEOUT` semantics.
- Added a controlled offline resolved-dependency fixture demonstrating a real
  dependency transition from version 1.0.0 to 1.1.0.
- Added AST-based detection and mutation of literal Python random seeds for
  `random.seed`, NumPy seed calls, and `torch.manual_seed`.
- Added a controlled random-seed fixture demonstrating both survived and
  killed reproducibility mutations.
- Added the `data-split` mutation operator for removing explicit
  `train_test_split` stratification.
- Added the `cv-fold-count` mutation operator for changing explicit
  cross-validation fold counts.
