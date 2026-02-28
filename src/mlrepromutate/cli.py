import typer

from mlrepromutate import __version__

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


if __name__ == "__main__":
    app()