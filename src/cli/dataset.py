import os
import sys
import shutil
import pprint
import yaml

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

import fairly

pp = pprint.PrettyPrinter(indent=4)

app = typer.Typer(pretty_exceptions_show_locals=False)

@app.command()
def create(
    metadata: str = typer.Argument(..., help="Metadata specification to be used for the dataset, for example figshare or zenodo."),
) -> None:
    '''Create a local dataset under path with default template
    
    fairly dataset create <path>

    Create a local dataset under path with the specified template
    <template> = 'zeondo, 4tu, default'
    
    fairly dataset create <path> --template <template>
    '''
    # Check that the manifest is not placed in the dataset directory
    if os.path.isfile("manifest.yaml"):
        print("manifest.yaml already exists in the current directory, cannot overwrite existing dataset metadata")
    else:
        template_path = os.path.join(os.path.dirname(fairly.__file__), './data/templates', f'{metadata}.yaml')
        shutil.copy(template_path, os.path.join(os.getcwd(), "manifest.yaml"))

@app.command()
def show():
    '''Show information about the specified local dataset
    show some metadata + handy info about the dataset
    fairly dataset show <path>
    '''
    raise NotImplementedError

@app.command()
def clone(
    url: str = typer.Option("", help="URL option argument"),
    token: str = typer.Option("", help="Token option argument"),
    # doi: str = typer.Option("", help="DOI option argument"),
    repo: str = typer.Option("", help="Repository option argument"),
    id: str = typer.Option("", help="ID option argument"),
    path: str = typer.Argument("./", help="Path where the dataset will be downloaded"),
) -> None:
    '''
    Clones a dataset by using its URL address, DOI or ID among other arguments
    
    Examples: \n
        >>> fairly dataset clone <url|doi> \n
        >>> fairly dataset clone https://zenodo.org/record/6026285 \n
        >>> fairly dataset clone url --token <token>  \n
        >>> fairly dataset clone <repository> <id> \n
        >>> fairly dataset clone --repo zenodo --id 6026285 \n
    '''
    # Test the connection to the repository by listing account datasets    
    dataset = None
    if url:
        arg = url # (uncomment when doi is implemented) if url else doi
        try:
            if token: dataset = fairly.dataset(arg, token=token)
            else: dataset = fairly.dataset(arg)
        except Exception as e: 
            print(e)
            return None

    elif repo:
        # Make sure that client is a valid client
        try: client = fairly.client(repo)
        except Exception as e: print(e)

        try: dataset = client.get_dataset(id)
        except Exception as e: 
            print(e)
            print("Please specify the dataset ID")
            return None
    try:
        dir_name = dataset.metadata['title'].replace(" ", "_").lower() 
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient = True,
        ) as progress:
            progress.add_task("Cloning dataset",total=None)
            dataset.store(f'{path}{dir_name}')
            print(f"Dataset {dir_name} successfully cloned to {path}{dir_name}")

    except Exception as e: 
        print("Probably you have already cloned this dataset in this directory.")
        raise e
    
@app.command()
def list(
    repository: str = typer.Argument("zenodo", help="Repository name"),
) -> None:
    '''List all datasets in the specified repository by doi, title, and publication_date'''
    # Test the connection to the repository by listing account datasets
    client = fairly.client(repository)
    try:
        # store dataset lists and print the id, url and title
        list = client.get_account_datasets()
        if len(list) == 0:
            print("There are no datasets under this account")
        else:
            print("\n")
            for dataset in list:
                # get the dataset metadata
                metadata = dataset.metadata
                item = {}
                for i in metadata:
                    if i == "publication_date": item[i] = metadata[i]
                    if i == 'title': item[i] = metadata[i]
                    if i == 'doi': item[i] = metadata[i]

                # pretty print the list of datasets with yaml format
                yaml.dump(item, sys.stdout)
                print("------------------")
        
        #TODO: Print the test_connection exception message
        # List datasets in readable format
    except:
        pass

@app.command()
def upload(
    repo: str = typer.Argument("", help="Repository option argument"),
    # path: str = typer.Argument("./", help="Path where the dataset will be uploaded"),
    token: str = typer.Option("", help="Token option argument"),
):
    '''
    Upload dataset by using a custom token (can be useful for e.g. data stewards)
    >>> fairly dataset upload <path> <repository> --token <token>
    >>> fairly upload <path> <repository> --token <token>
    
    If the dataset was not uploaded before: create remote entry (get id), set metadata, upload all files, upload local manifest to add id
    If the dataset was uploaded (id exists in manifest): update remote metadata, upload added and modified files, delete removed files
    '''
    # Check that the manifest is placed in the dataset directory
    # if manifest is not in path, raise error
    if not os.path.isfile(f"{os.getcwd()}/manifest.yaml"):
        print(os.path.exists(f"{path}manifest.yaml"))
        print(os.getcwd())
        print("manifest.yaml does not exist in the current directory, cannot upload dataset")
        return None
            
    try:
        path = "../"
        dataset = fairly.dataset(os.getcwd())
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
        # deconstruct the error message
        print(e)
        print(dataset.metadata)
        return None

@app.command()
def delete():
    '''
    fairly delete (url|doi)
    '''
    raise NotImplementedError

if __name__ == "__main__":
    app()