"""
fairly
"""
from typing import Dict, List

import os
import json
import pkgutil
import importlib
import shutil
import glob
from functools import lru_cache

from .client import Client
from .dataset import Dataset
from .dataset.local import LocalDataset
from .file import File


def get_config(prefix: str) -> Dict:
    """Returns configuration parameters for the specified prefix.

    Configuration parameters are read from the following sources:

    1. Configuration file of the user located at ``~/.fairly/config.json``.
    2. Environmental variables of the user.

    .. Attention:: Global and user-defined repository configuration files are not considered by this method.

    Args:
        prefix: Configuration prefix.

    Returns:
        Dictionary of configuration parameters for the specified prefix.

    Examples:
        >>> fairly.get_config("orcid")
        >>> {'client_id': 'id', 'client_secret': 'secret', ...}
    """
    config = {}

    # Read configuration from the user configuration file
    try:
        with open(os.path.expanduser("~/.fairly/config.json"), "r") as file:
            attrs = json.load(file)
            if prefix in attrs and isinstance(attrs[prefix], dict):
                config.update(attrs[prefix])
    except FileNotFoundError:
        pass

    # Read configuration from the environmental variables
    prefix = "FAIRLY_" + prefix.upper() + "_"
    start = len(prefix)
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        key = key[start:].lower()
        config[key] = val

    return config


# REMARK: @cache decorator can be used for Python 3.9+
@lru_cache(maxsize=None)
def get_clients() -> Dict:
    """Returns available clients.

    Returns:
        Dictionary of the available clients. Keys are client identifiers (str), values are client classes (Client).

    Raises:
        AttributeError: If a client module is not valid.

    Examples:
        >>> fairly.get_clients()
        >>> {'figshare': <class 'fairly.client.figshare.FigshareClient'>, ...}
    """
    clients = {}

    # For each client module
    for _, id, _ in pkgutil.iter_modules([os.path.join(__path__[0], "client")]):
        # Load module
        client = importlib.import_module(f"fairly.client.{id}")
        # Get client class name
        classname = client.CLASS_NAME
        if not classname:
            raise AttributeError(f"Invalid client module: {id}")
        # Set client class
        clients[id] = getattr(client, classname)

    # Return
    return clients


# REMARK: @cache decorator can be used for Python 3.9+
@lru_cache(maxsize=None)
def get_repositories() -> Dict:
    """Returns recognized repositories.

    Returns:
        Dictionary of the recognized repositories. Keys are repository identifiers (str), values are repository
        dictionaries (Dict).

    Raises:
        AttributeError: If a repository has no client id.
        AttributeError: If a repository has invalid client id.

    Examples:
        >>> fairly.get_repositories()
        >>> {'4tu': {'client_id': 'figshare', 'name': '4TU.ResearchData', 'url': 'https://data.4tu.nl/', ...}, ...}
    """
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

    # Create repository dictionary
    repositories = {}
    clients = get_clients()
    for id, attrs in data.items():
        repository = {}
        repository["id"] = id
        if "client_id" not in attrs:
            raise AttributeError(f"No client id: {id}")
        elif attrs["client_id"] not in clients:
            raise AttributeError(f"Invalid client_id: {id}")
        else:
            repository["client_id"] = attrs["client_id"]
        client = clients[repository["client_id"]]
        repository.update(client.get_config(**attrs))
        repositories[id] = repository

    # Return
    return repositories


# REMARK: @cache decorator can be used for Python 3.9+
@lru_cache(maxsize=None)
def metadata_templates() -> List:
    """Returns list of available metadata templates.

    Returns:
        List of available metadata templates (str).

    Examples:
        >>> fairly.metadata_templates()
        >>> ['default', 'zenodo', 'figshare']
    """
    templates = []

    for file in os.listdir(os.path.join(__path__[0], "data", "templates")):
        name, ext = os.path.splitext(file)
        if ext == ".yaml":
            # TODO: Check if a valid metadata template
            templates.append(name)

    return templates


def get_repository(uid: str) -> Dict:
    """Returns repository dictionary of the specified repository.

    Args:
        uid: Repository id or URL address.

    Returns:
        Repository dictionary if a recognized repository, ``None`` otherwise.

    Examples:
        >>> fairly.get_repository("4tu")
        >>> {'id': '4tu', 'client_id': 'figshare', 'name': '4TU.ResearchData', 'url': 'https://data.4tu.nl/', ...}

        >>> fairly.get_repository("5tu")
        >>>
    """
    repositories = get_repositories()

    if uid in repositories:
        return repositories[uid]

    for _, repository in repositories.items():
        if uid == repository["url"]:
            return repository

    return None


def client(id: str, **kwargs) -> Client:
    """Creates client object from a client or repository identifier.

    Identifier is first checked within recognized repository identifiers. If
    no match is found, it is regarded as a client identifier. Additional
    client arguments (e.g. API URL address) might be necessary for the later.

    Args:
        id (str): Client or repository identifier.
        **kwargs: Other client arguments.

    Returns:
        Client object.

    Raises:
        ValueError: If invalid client id.

    Examples:
        >>> # Create a 4TU.ResearchData client (id = "4tu")
        >>> client = fairly.client("4tu")

        >>> # Create a Figshare client with a custom URL address
        >>> client = fairly.client("figshare", url="https://data.4tu.nl/")
    """
    clients = get_clients()

    repository = get_repository(id)
    if repository:
        kwargs["repository_id"] = repository["id"]
        id = repository["client_id"]

    if id not in clients:
        raise ValueError(f"Invalid client id: {id}")

    return clients[id](**kwargs)


def dataset(id: str) -> Dataset:
    """Creates dataset object from a dataset identifier.

    The following types of dataset identifiers are supported:
        - DOI : Digital object identifier of the remote dataset.
        - URL : URL address of the remote dataset.
        - Path : Path of the local dataset.

    Repository of the dataset is automatically detected by checking the URL
    addresses and the DOI prefixes of the recognized repositories.

    Args:
        id (str): Dataset identifier.

    Returns:
        Dataset object.

    Raises:
        ValueError: If unknown dataset identifier.

    Examples:
        >>> dataset = fairly.dataset("10.5281/zenodo.6026285")
        >>> dataset = fairly.dataset("https://zenodo.org/record/6026285")
    """
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

    raise ValueError(f"Unknown dataset identifier: {id}")


def init_dataset(path: str, template: str = "default", manifest_file: str = "manifest.yaml", create: bool = True) -> LocalDataset:
    if not os.path.exists(path):
        if create:
            os.makedirs(path)
        else:
            raise ValueError(f"Invalid path: {path}")
    elif not os.path.isdir(path):
        raise NotADirectoryError

    manifest_path = os.path.join(path, manifest_file)
    if os.path.exists(manifest_path):
        raise ValueError("Operation not permitted")

    template_path = os.path.join(
        __path__[0], "data", "templates", f"{template}.yaml")
    if not os.path.exists(template_path):
        raise ValueError(f"Invalid template name: {template}")

    with open(template_path) as file:
        metadata = file.read()

    with open(manifest_path, "w") as file:
        file.write(f"{metadata}\nfiles:\n  includes: []\n  excludes: []\n")

    return dataset(path)


def notify(file: File, total_size: int) -> None:
    print(f"{file.path}, {file.size}/{total_size}")


if __name__ == "__main__":
    # TODO: CLI implementation
    raise NotImplementedError
