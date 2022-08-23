"""
fairly
"""
from typing import Dict, List

import re
import os
import json
import pkgutil
import importlib

from .client import Client
from .dataset.local import LocalDataset

_clients = None
_repositories = None

def get_config(prefix: str) -> Dict:
    """
    Returns:
      Dictionary of configuration attributes for the specified prefix
    >>> fairly.get_config("figshare")
    {'token': '1234567890'}
    """
    config = {}
    # Get configuration from the configuration file
    try:
        with open(os.path.expanduser("~/.fairly/config.json"), "r") as file:
            attrs = json.load(file)
            if prefix in attrs and isinstance(attrs[prefix], dict):
                config.update(attrs[prefix])
    except FileNotFoundError:
        pass
    # Get configuration from the environmental variables
    prefix = "FAIRLY_" + prefix.upper() + "_"
    start = len(prefix)
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        key = key[start:].lower()
        config[key] = val
    return config

def get_clients() -> Dict:
    """
    Returns a dictionary clients supported by the package.
    Keys of the dictionary are unique client identifiers (string).
    Values of the dictionary are client classes (Client).
    """
    global _clients
    # Return if clients are available
    if _clients is not None:
        return _clients
    clients = {}
    # For each client module
    for _, name, _ in pkgutil.iter_modules([os.path.join(__path__[0], "client")]):
        # Load module
        client = importlib.import_module(f"fairly.client.{name}")
        # Get client class name
        classname = client.CLASS_NAME
        if not classname:
            raise ValueError(f"No client class name {name}")
        # Set client class
        clients[name] = getattr(client, classname)
    # Set clients atomically
    _clients = clients
    # TODO: Return a deep copy to prevent modification
    return _clients

def get_repositories() -> List:
    global _repositories
    # Return if repositories are available
    if _repositories is not None:
        return _repositories
    # For each repository file path
    data = {}
    for path in [os.path.join(__path__[0], "data"), os.path.expanduser("~/.fairly")]:
        # Read repository file
        filename = os.path.join(path, "repositories.json")
        try:
            with open(filename, "r") as file:
                for id, attrs in json.load(file).items():
                    if id not in data:
                        data[id] = attrs
                    else:
                        data[id].update(attrs)
        except FileNotFoundError:
            pass
    repositories = {}
    clients = get_clients()
    for id, attrs in data.items():
        repository = {}
        repository["id"] = id
        if "client_id" not in attrs:
            raise ValueError(f"No client id {id}")
        elif attrs["client_id"] not in clients:
            raise ValueError(f"Invalid client_id {id}")
        else:
            repository["client_id"] = attrs["client_id"]
        client = clients[repository["client_id"]]
        repository.update(client.get_config(**attrs))
        repositories[id] = repository
    # Set repositories atomically
    _repositories = repositories
    # TODO: Return a deep copy to prevent modification
    return _repositories

def get_repository(id: str) -> Dict:
    repositories = get_repositories()
    if id in repositories:
        return repositories[id]
    for _, repository in repositories.items():
        if id == repository["url"]:
            return repository
    return None

def write_default_config(repositories: list) -> None:
    """
    Write the default configuration file
    >>> fairly.write_default_config()
    """
    # For each client generate a default configuration
    config = {}
    # Add repositories list to config
    config["repositories"] = []
    for id, repository in repositories.items():
        platform = { "platform": repository['client_id'], "token": "" }
        exists = platform in config["repositories"]
        if not exists:
            config["repositories"].append(platform)

    # Write the default configuration
    with open(os.path.expanduser("~/.fairly/config.json"), "w") as file:
        json.dump(config, file, indent=4)

def client(id: str, **kwargs) -> Client:
    """
    TODO: Explain how this is related to a configuration file

    """
    clients = get_clients()
    repository = get_repository(id)
    if repository:
        kwargs["repository_id"] = repository["id"]
        id = repository["client_id"]
    if id not in clients:
        raise ValueError("Invalid client id")
    return clients[id](**kwargs)

def get_local_dataset(path: str) -> LocalDataset:
    return LocalDataset(path)


def set_fairly_default_config():
    """
    Check if the ~/.fairly/config.json exists, if not create it
    """
    config_dir = os.path.expanduser("~/.fairly/")
    config_file = os.path.join(config_dir, "config.json")

    if not os.path.exists(config_dir):
        # Get the list of clients
        os.mkdir(config_dir)
        print("Created ~/.fairly directory")
    else:
        print("~/.fairly directory already exists")

    if not os.path.exists(config_file):
        print("Creating default config file")
        write_default_config(get_repositories())
    
    else:
        print("fairly config file already exists")

    print("Config file created at ~/.fairly/config.json")
    print("Consider adding your authentication tokens to the config file for the different repository platforms")

# We run this function to create the default config file
set_fairly_default_config()

    
if __name__ == "__main__":
    # TODO: CLI implementation
    raise NotImplementedError
