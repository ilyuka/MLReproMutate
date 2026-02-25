import typer

app = typer.Typer(
    help="Mutation testing for reproducibility safeguards in ML experiments."
)


@app.command()
def version() -> None:
    """Print the current MLReproMutate version."""
    from mlrepromutate import __version__

    typer.echo(__version__)


if __name__ == "__main__":
    app()