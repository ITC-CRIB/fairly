"""CLI module."""
import click

from .client import client
from .dataset import dataset
from .repository import repository


@click.group(
    help="fairly command-line tool.",
)
def cli():
    """Command group for main commands."""
    pass


# Register subcommands
cli.add_command(client)
cli.add_command(dataset)
cli.add_command(repository)


if __name__ == "__main__":
    cli()
