import typer
import fairly
import pprint

pp = pprint.PrettyPrinter(indent=4)

app = typer.Typer()

@app.command()
def list():
    '''List all repositories supported by fairly'''
    repositories = fairly.get_repositories()
    for key in repositories:
        print(key)

@app.command()
def list_my_datasets():
    '''List all datasets in the current repository'''
    raise NotImplementedError

@app.command()
def add(
    id: str = typer.Option("", help="Repository ID"),
):
    ''' Add a repository to the config file,
    
    fairly repository add --id <id> --name <name> --api-url <url> --token <token>

    Notice that this should only be allowed once there is a corresponing module
    for the repository.
    '''
    if id:
        print(f"Adding repository {id}")
        fairly.add_repository(id)

@app.command()
def show(name: str):
    ''' Show a repository details '''
    for key in fairly.get_repositories():
        if key == name:
            pp.pprint(fairly.get_repositories()[key])
            break
        else:
            print(f"Repository {name} not found")
            break

@app.command()
def update(
    id: str,
    token: str = typer.Option("", help="Repository token")
):
    ''' Update a repository token '''
    if token:
        # TODO: This method or something similar doesnt exist yet
        fairly.update_repository(id, token)

@app.command()
def remove():
    '''fairly repository remove <id>'''
    raise NotImplementedError

if __name__ == "__main__":
    app()

