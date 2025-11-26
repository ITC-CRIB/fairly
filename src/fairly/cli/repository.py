"""CLI Repository module."""
import click

import fairly
from . import common
from ..client import Client


@click.group(
    help="Repository commands.",
)
def repository():
    """Command group for repository-related commands."""
    pass


@repository.command(
    help="List repositories defined in the configuration files.",
)
@common.format_option
def list(format):
    """List repositories defined in the configuration files.

    `fairly repository list --format <format>`

    Args:
        format (str): Output format.
    """
    repositories = fairly.get_repositories()

    if format == 'text':
        for id, info in sorted(repositories.items()):
            click.echo(f"* {id}")
            for key, val in info.items():
                if key == 'id':
                    continue
                click.echo(f"  - {key}: {val}")
            click.echo()

    else:
        out = common.serialize(repositories, format)
        click.echo(out)


@repository.command(
    help="Add a repository to the configuration file.",
)
@click.argument(
    'client_id',
    type=click.Choice(fairly.get_clients().keys(), case_sensitive=False),
)
@click.argument('id')
@common.custom_options(Client.get_config_parameters())
@click.option(
    '--param',
    '-p',
    multiple=True,
    help="Other repository configuration parameters.",
)
def add(client_id, id, param, **kwargs):
    """Add a repository to the configuration file.

    fairly repository add <client_id> <id> --name <name> --api-url <url> --token <token>

    Args:
        client_id (str): Client identifier.
        id (str): Repository identifier.
        param (List): Custom repository configuration parameters (optional).
        **kwargs (Dict): Common repository configuration parameters (optional).

    Raises:
        NotImplementedError
    """
    kwargs = {key: val for key, val in kwargs.items() if val is not None}

    for item in param:
        if '=' in item:
            key, val = item.split('=', 1)
            kwargs[key] = val
        else:
            raise click.BadParameter(f"Invalid parameter {item}.")

    client = fairly.client(client_id, repository_id = id, **kwargs)

    raise NotImplementedError


@repository.command(
    help="Show configuration of a repository.",
)
@click.argument('id')
@common.format_option
def config(id, format):
    """Show configuration of a repository.

    `fairly repository config <id> --format <format>`

    Args:
        id (str): Repository identifier.
        format (str): Output format.
    """
    repository = fairly.get_repository(id)

    if not repository:
        raise click.UsageError("Invalid repository id.")

    if format == 'text':
        for key, val in repository.items():
            click.echo(f"- {key}: {val}")

    else:
        out = common.serialize(repository, format)
        click.echo(out)


@repository.command(
    help="Set access token of a repository in the configuration file.",
)
@click.argument('id')
@click.argument('token')
def token(id, token):
    """Set access token of a repository in the configuration file.

    `fairly repository token <id> <token>`

    Args:
        id (str): Repository identifier.
        token (str): Repository access token.
    """
    try:
        client = fairly.client(id, token=token)

    except ValueError as err:
        raise click.UsageError(err)

    client.save_config()

    click.echo(f"Access token of the `{id}` repository is set as `{token}`.")


@repository.command(
    help="Remove a repository from the configuration file.",
)
@click.argument('id')
def remove(id):
    """Remove a repository from the configuration file.

    `fairly repository remove <id>`

    Args:
        id (str): Repository identifier.

    Raises:
        NotImplementedError
    """
    raise NotImplementedError
