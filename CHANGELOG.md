# Changelog

All notable changes to MLReproMutate will be documented in this file.

The project is currently in early development and does not yet have a stable
public API.

## Unreleased
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