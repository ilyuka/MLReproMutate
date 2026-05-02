import shlex
from pathlib import Path
from typing import Annotated

import typer

from mlrepromutate import __version__
from mlrepromutate.engine import (
    BaselineValidationError,
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
from mlrepromutate.engine.runner import ExecutionResult
from mlrepromutate.models import MutationCandidate
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator
from mlrepromutate.reporting import (
    build_run_report,
    write_run_report,
)

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
    json_out: Annotated[
        Path | None,
        typer.Option(
            "--json-out",
            help="Write a machine-readable JSON report.",
        ),
    ] = None,
) -> None:
    """Evaluate dependency reproducibility mutations in a project."""

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
    except ValueError as exc:
        raise typer.BadParameter(
            str(exc),
            param_hint="--timeout",
        ) from exc

    evaluator = MutationEvaluator(runner)
    orchestrator = MutationOrchestrator(evaluator)
    operator = RelaxRequirementsPinOperator(
        requirements_file=requirements_file,
    )

    candidates = list(operator.detect(project))

    if not candidates:
        typer.echo("No applicable mutations found.")
        return

    typer.echo(f"Detected {len(candidates)} mutation candidates.")
    typer.echo("Validating baseline...")

    baseline_result: ExecutionResult | None = None

    def report_baseline_passed(
        result: ExecutionResult,
    ) -> None:
        nonlocal baseline_result
        baseline_result = result

        typer.echo(
            f"Baseline passed in {result.duration_seconds:.2f}s."
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
            requirements_file=requirements_file,
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