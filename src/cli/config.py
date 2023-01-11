import os
import pprint
import json

import yaml

import typer
import fairly

pp = pprint.PrettyPrinter(indent=4)

app = typer.Typer()

CONFIG_FILE = os.path.expanduser("~/.fairly/config.json")


# @app.command()
def add(
    id: str = typer.Argument("", help="Repository ID"),
):
    '''Add a repository to the config file,
    
    fairly repository add --id <id> --name <name> --api-url <url> --token <token>

    Notice that this should only be allowed once there is a corresponing module
    for the repository.
    '''
    raise NotImplementedError

@app.command()
def show(
    
):
    '''Show config details'''
        # expand user path
    print(f"You can edit the config file located at: {CONFIG_FILE}")

    print("FAIRLY CONFIG")
    print("--------------------")

    repos = fairly.get_repositories()
    print(yaml.dump(repos, default_flow_style=False))


@app.command()
def update_token(
    id: str = typer.Argument("", help="Repository ID"),
    token: str = typer.Argument("", help="Repository token")
):
    ''' Update a repository token os.path.expanduser('~/.fairly/config.json'''
    config = {}
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.loads(f.read())
            
            # check if token is already set with the same value
            if config[id]["token"] == token:
                print(f"Token for repository {id} is already set to {token}")
                return
            
            else: config[id]["token"] = token
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.write(json.dumps(config, indent=4))

    
    except FileNotFoundError:
        print(f"Config file not found at {CONFIG_FILE}")
        return



# @app.command()
def remove():
    '''fairly repository remove <id>'''
    raise NotImplementedError

if __name__ == "__main__":
    app()

