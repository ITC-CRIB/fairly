"""CLI module."""
import click

from .client import client
from .dataset import dataset
from .repository import repository


ART = r"""
______ ___  ___________ _       
|  ___/ _ \|_   _| ___ \ |      
| |_ / /_\ \ | | | |_/ / |_   _ 
|  _||  _  | | | |    /| | | | |
| |  | | | |_| |_| |\ \| | |_| |
\_|  \_| |_/\___/\_| \_|_|\__, |
                           __/ |
                          |___/ 
"""

@click.group(invoke_without_command=True, 
    help="fairly command-line tool.",
)
@click.pass_context
def cli(context):
    """Command group for main commands."""
    if context.invoked_subcommand is None:
        click.echo(ART)
        click.echo(context.get_help())


# Register subcommands
cli.add_command(client)
cli.add_command(dataset)
cli.add_command(repository)


if __name__ == "__main__":
    cli()
