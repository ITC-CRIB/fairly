"""CLI Dataset module."""
import click

import fairly
from . import common


@click.group(help="Dataset commands.")
def dataset():
    """Command group for dataset-related commands."""
    pass


@dataset.command()
@click.option(
    "--path",
    help="Path where the dataset will be initialized.",
)
@click.option(
    "--template",
    help="Metadata template to be used for the dataset. Templates maybe repository-specific and can be listed using `fairly template list`. The default template is compatible with all repositories.",
    default="default"
)
def init(path, template):
    """Initializes a local dataset with a metadata template.

    `fairly dataset create <path> --template <template>`
    \f
    Args:
        path (str): Path to initialize the local dataset.
        template (str): Metadata template (default = `default`)
    """
    # \f makes sure the text after that doesn't leak into the terminal. 
    fairly.init_dataset(path, template=template)


@dataset.command(
)
@click.option(
    "--id",
    help="Dataset identifier (URL, DOI, or unique ID).",
)
@click.option(
    "--path",
    help="Path where the dataset will be stored.",
)
@click.option(
    "--repository",
    help="Repository identifier.",
)
@click.option(
    "--token",
    help="Access token.",
)
@click.option(
    "--notify",
    is_flag=True,
    default=False,
    help="Enable progress notification.",
)
@click.option(
    "--extract",
    is_flag=True,
    default=False,
    help="Extract archive files",
)
def clone(id, path, repository, token, notify, extract):
    """Clones a dataset by using its URL address, DOI or unique ID.
    
    \b
    Examples:
        >>> fairly dataset clone https://zenodo.org/records/7759648
        >>> fairly dataset clone 10.5281/zenodo.7759648
        >>> fairly dataset clone --repository zenodo 7759648 --notify
    \f
    Args:
        id (str): Dataset identifier.
        path (str): Path to create the local dataset.
        repository (str): Repository identifier (optional).
        token (str): Access token (optional).
        notify (bool): Set True to enable progress notification (default = False)
        extract (bool): Set True to extract archive files (default = False)
    """
    if repository:
        if token:
            client = fairly.client(repository, token=token)
        else:
            client = fairly.client(repository)
        dataset = client.get_dataset(id)

    else:
        dataset = fairly.dataset(id)

    if not path:
        path = dataset.doi if dataset.doi else "dataset"

        for sep in ["/", "\\"]:
            path = path.replace(sep, "_")

    click.echo(f"Cloning dataset {id}...")

    dataset.store(path, notify=fairly.notify if notify else None, extract=extract)

    click.echo(f"Dataset {id} is successfully cloned to {path}.")


@dataset.command()
@click.option(
    "--path",
    help="Local dataset path.",
)
@click.option(
    "--repository",
    help="Repository identifier.",
)
@click.option(
    "--token",
    help="Access token.",
)
@click.option(
    "--notify",
    is_flag=True,
    help="Enable progress notification.",
)
def upload(path, repository, token, notify):
    """Uploads a local dataset to a data repository.
    \f
    Args:
        path (str): Local dataset path.
        repository (str): Repository identifier.
        token (str): Access token (optional).
        notify (bool): Set True to enable progress notification (default = False).
    """
    dataset = fairly.dataset(path)

    # TODO: Support repository selection from the metadata of the dataset.

    if token:
        client = fairly.client(repository, token=token)
    else:
        client = fairly.client(repository)

    click.echo(f"Uploading dataset {path}...")

    remote_dataset = dataset.upload(client, notify=fairly.notify if notify else None)

    click.echo(f"Dataset {path} is successfully uploaded at {remote_dataset.url}.")


@dataset.command()
@click.option(
    "--id",
    help="Dataset identifier (URL, DOI, or unique ID).",
)
@click.option(
    "--repository",
    help="Repository identifier.",
)
@click.option(
    "--token",
    help="Access token.",
)
def delete(id, repository, token):
    """Deletes a dataset by using its URL address, DOI or unique ID.
    \f
    Args:
        id (str): Dataset identifier.
        repository (str): Repository identifier (optional).
        token (str): Access token (optional).
    """
    if repository:
        if token:
            client = fairly.client(repository, token=token)
        else:
            client = fairly.client(repository)
        dataset = client.get_dataset(id)

    else:
        dataset = fairly.dataset(id)
        client = dataset.client

    click.echo(f"Deleting dataset {id}...")

    client.delete_dataset(dataset.id)

    click.echo(f"Dataset {id} is successfully deleted.")


@dataset.command
@click.option(
    "--repository",
    help="Repository identifier.",
)
def list(repository):
    """List all user datasets in a repository.
    \f
    Args:
        repository (str): Repository identifier.
    """
    # Test the connection to the repository by listing account datasets
    try:
        client = fairly.client(repository)
        datasets = client.get_account_datasets()
        if not datasets:
            click.echo("There are no user datasets.")
        else:
            for dataset in datasets:
                metadata = dataset.metadata
                item = {}
                for key in metadata:
                    if key in ["publication_date", "title", "doi"]:
                        item[key] = metadata[key]

                out = common.serialize(item, 'yaml')
                click.echo(out)
                click.echo()

    except Exception as e:
        click.echo(e, err=True)
        click.echo("Please specify a valid repository identifier.")