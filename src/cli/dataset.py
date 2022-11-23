import os
import sys
import shutil
import pprint
import yaml

import typer
import fairly

from cli import test_connection

pp = pprint.PrettyPrinter(indent=4)

app = typer.Typer(pretty_exceptions_show_locals=False)

@app.command()
def create(
    metadata: str = typer.Argument("", help="Metadata specification to be used for the dataset, for example figshare or zenodo."),
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
        fairly_path = os.path.dirname(fairly.__file__)
        template_path = os.path.join(fairly_path, "data","templates", f'{metadata}.yaml')
        shutil.copy(template_path, os.path.join(os.getcwd(), "manifest.yaml"))

@app.command()
def show():
    '''Show information about the specified local dataset
    show some metadata + handy info about the dataset
    fairly dataset show <path>
    '''
    raise NotImplementedError


@app.command()
def download(
    url: str = typer.Option("", help="URL option argument"),
    doi: str = typer.Option("", help="DOI option argument"),
    path: str = typer.Argument("./", help="Path where the dataset will be downloaded"),
) -> None:
    '''Download a dataset by using its URL address, DOI or ID'
    Download a dataset by using its URL address or DOI
    fairly automatically recognize them and creates corresponding client
    
    fairly dataset download <url|doi>
    fairly download <url|doi>
    
    Example: 
    >>> fairly download https://zenodo.org/record/6026285

    fairly dataset download <url|doi> --token <token> 
    fairly dataset download <repository> <id>
    fairly dataset download --repository zenodo --id 6026285
    '''
    # Test the connection to the repository by listing account datasets

    # Fetch the dataset metadata
    # stire the dataset metadata in the manifest
    raise NotImplementedError

@app.command()
def list(
    repository: str = typer.Argument("zenodo", help="Repository name"),
) -> None:
    '''List all datasets in the specified repository by doi, title, and publication_date'''
    # Test the connection to the repository by listing account datasets
    c = fairly.client(repository)
    try:
        if test_connection(c) == True:
        # if test_connection(c) == True:
            # store dataset lists and print the id, url and title
            l = c.get_account_datasets()
            if len(l) == 0:
                print("There are no datasets under this account")
            else:
                print("\n")
                for dataset in l:
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
def upload():
    '''
    Upload dataset by using a custom token (can be useful for e.g. data stewards)
    >>> fairly dataset upload <path> <repository> --token <token>
    >>> fairly upload <path> <repository> --token <token>
    
    If the dataset was not uploaded before: create remote entry (get id), set metadata, upload all files, upload local manifest to add id
    If the dataset was uploaded (id exists in manifest): update remote metadata, upload added and modified files, delete removed files
    '''
    # Raise error not implemented
    raise NotImplementedError

@app.command()
def delete():
    '''
    fairly delete (url|doi)
    '''
    raise NotImplementedError

if __name__ == "__main__":
    app()