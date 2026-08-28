import shlex
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from mlrepromutate import __version__
from mlrepromutate.engine import (
    BaselineValidationError,
    CommandResolutionError,
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
from mlrepromutate.engine.environment import VirtualEnvironmentResolver
from mlrepromutate.engine.resolved_dependency import (
    ResolvedDependencyEvaluator,
)
from mlrepromutate.engine.runner import ExecutionResult
from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.data_split import (
    RemoveTrainTestSplitStratificationOperator,
)
from mlrepromutate.operators.dependency import (
    RelaxRequirementsPinOperator,
)
from mlrepromutate.operators.evaluation_protocol import (
    ChangeCrossValidationFoldCountOperator,
)
from mlrepromutate.operators.randomness import (
    ChangePythonRandomSeedOperator,
)
from mlrepromutate.reporting import (
    build_run_report,
    write_run_report,
)


class OperatorName(StrEnum):
    DEPENDENCY_PIN = "dependency-pin"
    RANDOM_SEED = "random-seed"
    DATA_SPLIT = "data-split"
    CV_FOLD_COUNT = "cv-fold-count"


class DependencyMode(StrEnum):
    MANIFEST = "manifest"
    RESOLVED = "resolved"


app = typer.Typer(
    name="mlrepromutate",
    help="Mutation testing for reproducibility safeguards in ML experiments.",
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """MLReproMutate command-line interface."""


@app.command()
def version() -> None:
    """Print the current MLReproMutate version."""

    typer.echo(__version__)


@app.command()
def run(
    project: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            resolve_path=True,
            help="Project directory to evaluate.",
        ),
    ],
    command: Annotated[
        str,
        typer.Option(
            "--command",
            "-c",
            help='Validation command, for example: "python validate.py".',
        ),
    ],
    operator_name: Annotated[
        OperatorName,
        typer.Option(
            "--operator",
            help="Mutation operator to evaluate.",
        ),
    ] = OperatorName.DEPENDENCY_PIN,
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            help="Validation timeout in seconds.",
        ),
    ] = 300.0,
    requirements_file: Annotated[
        Path | None,
        typer.Option(
            "--requirements-file",
            help=(
                "Restrict dependency mutations to one requirements file "
                "relative to the project root."
            ),
        ),
    ] = None,
    dependency_mode: Annotated[
        DependencyMode,
        typer.Option(
            "--dependency-mode",
            help=(
                "Dependency evaluation mode: manifest only or "
                "fresh resolved environments."
            ),
        ),
    ] = DependencyMode.MANIFEST,
    python_file: Annotated[
        Path | None,
        typer.Option(
            "--python-file",
            help=(
                "Restrict Python source mutations to one file "
                "relative to the project root."
            ),
        ),
    ] = None,
    candidate_index: Annotated[
        int | None,
        typer.Option(
            "--candidate-index",
            help=(
                "Evaluate only one detected mutation candidate "
                "using its 1-based index."
            ),
        ),
    ] = None,
    json_out: Annotated[
        Path | None,
        typer.Option(
            "--json-out",
            help="Write a machine-readable JSON report.",
        ),
    ] = None,
) -> None:
    """Evaluate reproducibility mutations in a project."""

    command_parts = shlex.split(command)

    if not command_parts:
        raise typer.BadParameter(
            "Validation command must not be empty.",
            param_hint="--command",
        )

    try:
        runner = ExperimentRunner(
            command_parts,
            timeout_seconds=timeout,
        )
    except CommandResolutionError as exc:
        raise typer.BadParameter(
            str(exc),
            param_hint="--command",
        ) from exc
    except ValueError as exc:
        raise typer.BadParameter(
            str(exc),
            param_hint="--timeout",
        ) from exc

    if operator_name is OperatorName.DEPENDENCY_PIN:
        if python_file is not None:
            raise typer.BadParameter(
                "--python-file is only valid with --operator "
                "random-seed, data-split, or cv-fold-count.",
                param_hint="--python-file",
            )

        operator = RelaxRequirementsPinOperator(
            requirements_file=requirements_file,
        )

        operator_configuration = {
            "requirements_file": (
                str(requirements_file)
                if requirements_file is not None
                else None
            ),
            "dependency_mode": dependency_mode.value,
        }

        if dependency_mode is DependencyMode.RESOLVED:
            if requirements_file is None:
                raise typer.BadParameter(
                    "--dependency-mode resolved requires "
                    "--requirements-file."
                )

            executable_name = Path(runner.command[0]).name

            if not executable_name.startswith("python"):
                raise typer.BadParameter(
                    "--dependency-mode resolved currently requires "
                    "a Python validation command."
                )

            bootstrap_python = Path(runner.command[0])

            resolver = VirtualEnvironmentResolver(
                bootstrap_python=bootstrap_python,
                timeout_seconds=timeout,
            )

            evaluator = ResolvedDependencyEvaluator(
                runner=runner,
                resolver=resolver,
                requirements_file=requirements_file,
            )
        else:
            evaluator = MutationEvaluator(runner)

    elif operator_name is OperatorName.RANDOM_SEED:
        if requirements_file is not None:
            raise typer.BadParameter(
                "--requirements-file is only valid with "
                "--operator dependency-pin.",
                param_hint="--requirements-file",
            )

        if dependency_mode is DependencyMode.RESOLVED:
            raise typer.BadParameter(
                "--dependency-mode resolved is only valid with "
                "--operator dependency-pin.",
                param_hint="--dependency-mode",
            )

        operator = ChangePythonRandomSeedOperator(
            python_file=python_file,
        )

        operator_configuration = {
            "python_file": (
                str(python_file)
                if python_file is not None
                else None
            ),
        }

        evaluator = MutationEvaluator(runner)

    elif operator_name is OperatorName.DATA_SPLIT:
        if requirements_file is not None:
            raise typer.BadParameter(
                "--requirements-file is only valid with "
                "--operator dependency-pin.",
                param_hint="--requirements-file",
            )

        if dependency_mode is DependencyMode.RESOLVED:
            raise typer.BadParameter(
                "--dependency-mode resolved is only valid with "
                "--operator dependency-pin.",
                param_hint="--dependency-mode",
            )

        operator = RemoveTrainTestSplitStratificationOperator(
            python_file=python_file,
        )

        operator_configuration = {
            "python_file": (
                str(python_file)
                if python_file is not None
                else None
            ),
        }

        evaluator = MutationEvaluator(runner)

    else:
        if requirements_file is not None:
            raise typer.BadParameter(
                "--requirements-file is only valid with "
                "--operator dependency-pin.",
                param_hint="--requirements-file",
            )

        if dependency_mode is DependencyMode.RESOLVED:
            raise typer.BadParameter(
                "--dependency-mode resolved is only valid with "
                "--operator dependency-pin.",
                param_hint="--dependency-mode",
            )

        operator = ChangeCrossValidationFoldCountOperator(
            python_file=python_file,
        )

        operator_configuration = {
            "python_file": (
                str(python_file)
                if python_file is not None
                else None
            ),
        }

        evaluator = MutationEvaluator(runner)

    if candidate_index is not None:
        operator_configuration["candidate_index"] = candidate_index

    orchestrator = MutationOrchestrator(evaluator)

    try:
        candidates = list(operator.detect(project))
    except (ValueError, FileNotFoundError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    if not candidates:
        typer.echo("No applicable mutations found.")
        return

    detected_count = len(candidates)
    typer.echo(
        f"Detected {detected_count} mutation candidates."
    )

    if candidate_index is not None:
        if candidate_index < 1 or candidate_index > detected_count:
            raise typer.BadParameter(
                "Candidate index must be between 1 and "
                f"{detected_count}.",
                param_hint="--candidate-index",
            )

        candidates = [candidates[candidate_index - 1]]

        typer.echo(
            f"Selected mutation candidate "
            f"{candidate_index} of {detected_count}."
        )

    typer.echo("Validating baseline...")

    baseline_result: ExecutionResult | None = None

    def report_baseline_passed(
        result: ExecutionResult,
    ) -> None:
        nonlocal baseline_result
        baseline_result = result

        evaluator_metadata = evaluator.run_metadata()
        baseline_resolution = evaluator_metadata.get(
            "baseline_resolution"
        )

        if isinstance(baseline_resolution, dict):
            resolution_seconds = baseline_resolution.get(
                "duration_seconds"
            )

            if isinstance(resolution_seconds, int | float):
                typer.echo(
                    "Baseline environment resolved in "
                    f"{resolution_seconds:.2f}s."
                )

        typer.echo(
            f"Baseline validation passed in "
            f"{result.duration_seconds:.2f}s."
        )

    def report_candidate_start(
        index: int,
        total: int,
        candidate: MutationCandidate,
    ) -> None:
        line_number = candidate.metadata.get("line_number")

        location = str(candidate.target)

        if isinstance(line_number, int):
            location = f"{location}:{line_number}"

        typer.echo()
        typer.echo(f"[{index}/{total}] {location}")
        typer.echo(f"  {candidate.description}")

    def report_candidate_result(
        index: int,
        total: int,
        result,
    ) -> None:
        del index, total

        typer.echo(
            f"  {result.outcome.value.upper()}: {result.reason}"
        )

    try:
        results = orchestrator.run(
            project,
            operator,
            candidates=candidates,
            on_baseline_passed=report_baseline_passed,
            on_candidate_start=report_candidate_start,
            on_candidate_result=report_candidate_result,
        )
    except BaselineValidationError as exc:
        typer.echo(f"Baseline error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if json_out is not None:
        if baseline_result is None:
            raise RuntimeError(
                "Baseline result is unavailable after a successful run."
            )

        report = build_run_report(
            project_root=project,
            validation_command=command,
            timeout_seconds=timeout,
            operator=operator,
            baseline=baseline_result,
            results=results,
            operator_configuration=operator_configuration,
            evaluator_metadata=evaluator.run_metadata(),
        )

        write_run_report(
            json_out,
            report,
        )

        typer.echo()
        typer.echo(f"JSON report: {json_out}")

    if not results:
        typer.echo("No applicable mutations found.")
        return

    killed = sum(
        result.outcome.value == "killed"
        for result in results
    )
    survived = sum(
        result.outcome.value == "survived"
        for result in results
    )

    typer.echo()
    typer.echo(
        f"Summary: {len(results)} mutations, "
        f"{killed} killed, {survived} survived."
    )


if __name__ == "__main__":
    app()
