import os
import pprint

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

import fairly

pp = pprint.PrettyPrinter(indent=4)

app = typer.Typer(pretty_exceptions_show_locals=False)

@app.command()
def create(
    path: str = typer.Argument("", help="Path where the dataset will be created"),
    template: str = typer.Option("default", help="Metadata template to be used for the dataset"),
) -> None:
    '''Create a local dataset under path with default template\n

    fairly dataset create <path>\n

    Create a local dataset under path with the specified template\n
    <template> = 'zeondo, 4tu, default'\n

    fairly dataset create <path> --template <template>
    '''
    # Check that the manifest is not placed in the dataset directory
    if os.path.isfile("manifest.yaml"):
        print("manifest.yaml already exists in the current directory, cannot overwrite existing dataset metadata")
    else:
        fairly.init_dataset(path, template=template)
        return None

@app.command()
def clone(
    token: str = typer.Option("", help="Token option argument"),
    repo: str = typer.Option("", help="Repository option argument"),
    notify: bool = typer.Option(False, help="Enable process notification"),
    extract: bool = typer.Option(False, help="Extract archive files"),
    id: str = typer.Argument("", help="Dataset identifier (URL, DOI, or ID)"),
    path: str = typer.Argument("", help="Path where the dataset will be downloaded"),
) -> None:
    '''
    Clones a dataset by using its URL address, DOI or ID among other arguments

    Examples: \n
        >>> fairly dataset clone <url|doi> \n
        >>> fairly dataset clone https://zenodo.org/record/6026285 \n
        >>> fairly dataset clone <repository> <id> \n
        >>> fairly dataset clone --repo zenodo 6026285 \n
    '''

    if repo:
        try:
            client = fairly.client(repo)
        except Exception as e:
            print(e)
            return None

        dataset = client.get_dataset(id, token=token)
    
    else:
        dataset = fairly.dataset(id)

    try:
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
            print(f"Dataset is successfully cloned to {path}")

    except Exception as e:
        print(e)
        return None
        
    return None

@app.command()
def upload(
    path: str = typer.Argument("", help="Path where the dataset is located"),
    repo: str = typer.Argument("", help="Repository option argument"),
    token: str = typer.Option("", help="Token option argument"),
):
    '''
    Upload dataset by using a custom token (can be useful for e.g. data stewards)
    >>> fairly dataset upload <path> <repository> --token <token>
    >>> fairly upload <path> <repository> --token <token>

    If the dataset was not uploaded before: create remote entry (get id), set metadata, upload all files, upload local manifest to add id
    If the dataset was uploaded (id exists in manifest): update remote metadata, upload added and modified files, delete removed files
    '''
    try:
        dataset = fairly.dataset(path)

        if token:
            client = fairly.client(repo, token=token)
        else:
            client = fairly.client(repo)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient = True,
        ) as progress:
            progress.add_task(description="Uploading dataset...", total=None)
            remote_dataset = dataset.upload(client)
            print(f"Dataset successfully uploaded at {remote_dataset.url}")
        return None

    except ValueError as e:
        print(e)
        print(dataset.metadata)
        return None

@app.command()
def delete(
    repo: str = typer.Argument("", help="Repository option argument"),
    url: str = typer.Argument("", help="URL argument, url where the dataset to delete is located"),
):
    '''
    fairly delete (url|doi)
    '''
    try:
        dataset = fairly.dataset(url)

        # here we get the repository id from the url to create the client that
        # will be used to delete the dataset
        client = fairly.client(dataset._client._client_id)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient = True,
        ) as progress:
            progress.add_task(description="Deleting dataset...", total=None)
            client._delete_dataset(dataset.id)

        print(f"Dataset with id: { dataset.id['id'] } successfully deleted from {repo}")

    except Exception as e:
        raise

if __name__ == "__main__":
    app()