import sys
import pprint as pp

import yaml
import typer
import fairly

import cli.dataset
import cli.config



app = typer.Typer()
app.add_typer(cli.dataset.app, name="dataset")
app.add_typer(cli.config.app, name="config")

@app.command()
def list_repos():
    '''List all repositories supported by fairly'''
    repositories = fairly.get_repositories()

    print("List of repositories to use with fairly:")
    
    for key in repositories:
        print("- " + key)

@app.command()
@app.command()
def list_user_datasets(
    repository: str = typer.Argument("", help="Repository name"),
) -> None:
    '''List all datasets in the specified repository by doi, title, and publication_date'''
    # Test the connection to the repository by listing account datasets
    try:
        client = fairly.client(repository)
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

    except Exception as e: 
        print(e)
        print("Please specify a repository name that is valid")
    return None

if __name__ == "__main__":
    app()