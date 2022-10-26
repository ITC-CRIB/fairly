import typer

import cli.dataset
import cli.repository

app = typer.Typer()
app.add_typer(cli.dataset.app, name="dataset")
app.add_typer(cli.repository.app, name="repository")

if __name__ == "__main__":
    app()