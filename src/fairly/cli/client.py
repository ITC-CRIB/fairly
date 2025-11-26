"""CLI Client module."""
import click
import textwrap

import fairly
from . import common


@click.group(
    help="Client commands.",
)
def client():
    """Command group for client-related commands."""
    pass


@client.command(
    help="List supported clients.",
)
@common.format_option
def list(format):
    """List supported clients.

    Args:
        format (str): Output format.
    """
    clients = {}

    for id, client in fairly.get_clients().items():
        info = client.get_client_info()
        clients[id] = {
            'name': info.name,
            'description': info.description,
            'config_parameters': client.get_config_parameters(),
            'supports_folders': client.supports_folders(),
        }

    if format == 'text':
        click.echo("# Supported Clients")
        click.echo()

        for id, client in clients.items():
            click.echo(f"## {client['name']} (id = `{id}`)")
            click.echo()
            click.echo(textwrap.fill(client['description']))
            click.echo()
            click.echo(f"Supports folders: {'Yes' if client['supports_folders'] else 'No'}")
            click.echo()
            click.echo("**Configuration parameters:**")
            click.echo()
            for key, val in client['config_parameters'].items():
                click.echo(f"- `{key}`: {val}")
            click.echo()

    else:
        out = common.serialize(clients, format)
        click.echo(out)
