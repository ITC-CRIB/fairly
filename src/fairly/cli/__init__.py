"""CLI module."""
import click

from .client import client
from .dataset import dataset
from .repository import repository
from fairly._version import __version__

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

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

@click.group(context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    help="fairly command-line tool.",
)
@click.version_option(__version__, "-v", "--version", message="%(prog)s version %(version)s")
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
