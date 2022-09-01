"""
fairly
"""
from typing import Dict, List

import os
import json
import pkgutil
import importlib

from .client import Client
from .dataset import Dataset
from .dataset.local import LocalDataset

_clients = None
_repositories = None


# TODO: complete docstrings for these functions.

def get_config(prefix: str) -> Dict:
    """
    Params:
        prefix: ?????

    Returns:
      Dictionary of configuration attributes for the specified prefix

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
    Returns a dictionary of clients supported by the package.
    Keys of the dictionary are unique client identifiers (str).
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


def get_repositories() -> Dict:
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


def client(id: str, **kwargs) -> Client:
    clients = get_clients()
    repository = get_repository(id)
    if repository:
        kwargs["repository_id"] = repository["id"]
        id = repository["client_id"]
    if id not in clients:
        raise ValueError("Invalid client id")
    return clients[id](**kwargs)


def dataset(id: str) -> Dataset:
    key, val = Client.parse_id(id)

    if key == "url":
        for repository_id, repository in get_repositories().items():
            url = repository.get("url")
            if url and val.startswith(url):
                return client(repository_id).get_dataset(id)

    elif key == "doi":
        for repository_id, repository in get_repositories().items():
            for prefix in repository.get("doi_prefixes", []):
                if prefix and val.startswith(prefix):
                    return client(repository_id).get_dataset(id)

    else:
        return LocalDataset(id)

    raise ValueError("Unknown dataset identifier")


def notify(file, total_size) -> None:
    print(f"{file.path}, {file.size}/{total_size}")


if __name__ == "__main__":
    # TODO: CLI implementation
    raise NotImplementedError
