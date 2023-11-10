import typer

from rich.progress import Progress, SpinnerColumn, TextColumn

import fairly


app = typer.Typer(pretty_exceptions_show_locals=False)

@app.command()
def create(
    path: str = typer.Argument(help="Path where the dataset will be created"),
    template: str = typer.Option("default", help="Metadata template to be used for the dataset"),
) -> None:
    '''Create a local dataset under path with default template\n

    fairly dataset create <path>\n

    Create a local dataset under path with the specified template\n
    <template> = 'zeondo, 4tu, default'\n

    fairly dataset create <path> --template <template>
    '''
    fairly.init_dataset(path, template=template)


@app.command()
def clone(
    id: str = typer.Argument(help="Dataset identifier (URL, DOI, or unique ID)"),
    path: str = typer.Argument("", help="Path where the dataset will be stored"),
    repo: str = typer.Option("", help="Repository option argument"),
    token: str = typer.Option("", help="Access token option argument"),
    notify: bool = typer.Option(False, help="Enable process notification"),
    extract: bool = typer.Option(False, help="Extract archive files"),
) -> None:
    '''
    Clones a dataset by using its URL address, DOI or unique ID.

    Examples: \n
        >>> fairly dataset clone <url|doi|uid> \n \n
        >>> fairly dataset clone https://zenodo.org/record/7759648 \n
        >>> fairly dataset clone 10.5281/zenodo.7759648 \n
        >>> fairly dataset clone <repository> <id> \n
        >>> fairly dataset clone --repo zenodo 7759648 \n
    '''

    if repo:
        client = fairly.client(repo, token=token)
        dataset = client.get_dataset(id)

    else:
        dataset = fairly.dataset(id)

    if not path:
        path = dataset.doi if dataset.doi else "dataset"

        for sep in ["/", "\\"]:
            path = path.replace(sep, "_")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient = True,
    ) as progress:
        progress.add_task("Cloning dataset", total=None)

        dataset.store(path, notify=fairly.notify if notify else None, extract=extract)
        print(f"Dataset {id} is successfully cloned to {path}")


    return None

@app.command()
def upload(
    path: str = typer.Argument(help="Path where the dataset is located"),
    repo: str = typer.Argument(help="Repository to upload the dataset"),
    token: str = typer.Option(None, help="Access token option argument"),
    notify: bool = typer.Option(False, help="Enable process notification"),
):
    '''
    Uploads a local dataset to a data repository.
    '''
    dataset = fairly.dataset(path)

    # TODO: Support repository selection from the metadata template of the dataset

    if token:
        client = fairly.client(repo, token=token)
    else:
        client = fairly.client(repo)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient = True,
    ) as progress:
        progress.add_task(description=f"Uploading dataset {path}", total=None)
        remote_dataset = dataset.upload(client, notify=notify)

    print(f"Dataset {path} is successfully uploaded at {remote_dataset.url or remote_dataset.doi}")


@app.command()
def delete(
    id: str = typer.Argument(help="Dataset identifier (URL address, DOI, or unique ID)"),
    repo: str = typer.Option("", help="Repository option argument"),
    token: str = typer.Option("", help="Access token option argument"),
):
    '''
    Deletes a dataset by using its URL address, DOI or unique ID.
    '''
    if repo:
        client = fairly.client(repo, token=token)
        dataset = client.get_dataset(id)

    else:
        dataset = fairly.dataset(id)
        client = dataset.client

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient = True,
    ) as progress:
        progress.add_task(description="Deleting dataset {id}", total=None)
        client.delete_dataset(dataset.id)

    print(f"Dataset {id} is successfully deleted.")


if __name__ == "__main__":
    app()