import shlex
from pathlib import Path

import typer

from mlrepromutate import __version__
from mlrepromutate.engine import (
    BaselineValidationError,
    ExperimentRunner,
    MutationEvaluator,
    MutationOrchestrator,
)
from mlrepromutate.operators.dependency import RelaxRequirementsPinOperator

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
    project: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
        help="Project directory to evaluate.",
    ),
    command: str = typer.Option(
        ...,
        "--command",
        "-c",
        help='Validation command, for example: "python validate.py".',
    ),
    timeout: float = typer.Option(
        300.0,
        "--timeout",
        help="Validation timeout in seconds.",
    ),
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
    operator = RelaxRequirementsPinOperator()

    try:
        results = orchestrator.run(project, operator)
    except BaselineValidationError as exc:
        typer.echo(f"Baseline error: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if not results:
        typer.echo("No applicable mutations found.")
        return

    for result in results:
        typer.echo(
            f"{result.outcome.value.upper()}: "
            f"{result.candidate.description}"
        )

        if result.reason is not None:
            typer.echo(f"  {result.reason}")

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