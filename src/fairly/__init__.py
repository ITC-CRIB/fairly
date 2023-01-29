"""
fairly
"""
from typing import Dict, List

import sys
import os
import json
import pkgutil
import importlib
from functools import lru_cache

from .client import Client
from .dataset import Dataset
from .dataset.local import LocalDataset
from .file import File


def is_testing() -> bool:
    """Returns unit testing state.

    Returns:
        True if performing unit tests, False otherwise
    """
    return getattr(sys.modules[__name__], "TESTING", False)


def get_environment_config(key: str) -> Dict:
    """Returns configuration parameters for the specified key from environmental variables.

    Args:
        key (str): Configuration key.

    Returns:
        Dictionary of configuration parameters for the specified key.

    Examples:
        >>> fairly.get_environment_config("fairly")
        >>> {'orcid_client_id': 'id', ...}
    """
    config = {}

    prefix = "FAIRLY_" + key.upper() + "_"
    start = len(prefix)
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        key = key[start:].lower()
        config[key] = val

    return config


def get_config(key: str) -> Dict:
    """Returns configuration parameters for the specified key.

    Configuration parameters are read from the following sources:

    1. Configuration file of the package located at ``{package_root}/data/config.json``
    2. Configuration file of the user located at ``~/.fairly/config.json``.
    3. Environmental variables of the user starting with ``FAIRLY_{KEY}_``.

    Args:
        key (str): Configuration key.

    Returns:
        Dictionary of configuration parameters for the specified key.

    Examples:
        >>> fairly.get_config("fairly")
        >>> {'orcid_client_id': 'id', 'orcid_client_secret': 'secret', ...}
    """
    config = {}

    # For each configuration path
    for path in [os.path.join(__path__[0], "data"), os.path.expanduser("~/.fairly")]:
        # Read configuration for the configuration file if available
        try:
            with open(os.path.join(path, "config.json"), "r") as file:
                data = json.load(file)
                if key in data and isinstance(data[key], dict):
                    config.update(data[key])
        except FileNotFoundError:
            pass

    # Update configuration from the environment variables
    config.update(get_environment_config(key))

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
        ValueError: If configuration is invalid.
        AttributeError: If a repository has no client id.
        AttributeError: If a repository has invalid client id.

    Examples:
        >>> fairly.get_repositories()
        >>> {'4tu': {'client_id': 'figshare', 'name': '4TU.ResearchData', 'url': 'https://data.4tu.nl/', ...}, ...}
    """
    data = {}

    # Set configuration paths
    paths = [os.path.join(__path__[0], "data")]
    if not is_testing():
        paths.append(os.path.expanduser("~/.fairly"))

    # For each configuration path
    for path in paths:
        # Read repository configuration from the configuration file
        try:
            with open(os.path.join(path, "config.json"), "r") as file:
                for key, val in json.load(file).items():
                    if key == "fairly":
                        continue

                    elif not isinstance(val, dict):
                        raise ValueError(f"Invalid configuration {path}: {key}")

                    elif key not in data:
                        data[key] = val

                    else:
                        data[key].update(val)

        except FileNotFoundError:
            pass

    # Update repository configuration from the environment variables if not testing
    if not is_testing():
        for key in data:
            data[key].update(get_environment_config(key))

    # Create repository dictionary
    repositories = {}
    clients = get_clients()

    for id, attrs in data.items():
        repository = {}

        repository["id"] = id

        if "client_id" not in attrs:
            raise AttributeError(f"No client id {id}")
        elif attrs["client_id"] not in clients:
            raise AttributeError(f"Invalid client_id {id}:{attrs['client_id']}")
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
        uid (str): Repository id or URL address.

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
        return repositories[uid].copy()

    for _, repository in repositories.items():
        if uid == repository["url"]:
            return repository.copy()

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
    if isinstance(id, str):
        key, val = Client.parse_id(id)
    else:
        key = None

    if key == "url":
        for repository_id, repository in get_repositories().items():
            url = repository.get("url")
            if url and val.startswith(url):
                return client(repository_id).get_dataset(url=val)

    elif key == "doi":
        for repository_id, repository in get_repositories().items():
            for prefix in repository.get("doi_prefixes", []):
                if prefix and val.startswith(prefix):
                    return client(repository_id).get_dataset(doi=val)

    else:
        return LocalDataset(id)

    raise ValueError(f"Unknown dataset identifier: {id}")


def init_dataset(path: str, template: str = "default", create: bool = True) -> LocalDataset:
    """Initializes a local dataset.

    Args:
        path (str): Local path of the dataset.
        template: Template of the dataset (default = 'default').
        create: Set True to create the dataset directory if not exists (default = True)

    Returns:
        Local dataset object

    Raises:
        ValueError("Invalid path"): If path is invalid.
        NotADirectoryError: If path is not a directory path.
        ValueError("Operation not permitted"): If path is an existing dataset path.
        ValueError("Invalid template name"): If template name is invalid.

    """
    if not os.path.exists(path):
        if create:
            os.makedirs(path)
        else:
            raise ValueError("Invalid path")
    elif not os.path.isdir(path):
        raise NotADirectoryError

    manifest_path = os.path.join(path, "manifest.yaml")
    if os.path.exists(manifest_path):
        raise ValueError("Operation not permitted")

    template_path = os.path.join(__path__[0], "data", "templates", f"{template}.yaml")
    if not os.path.exists(template_path):

        repository = get_repository(template)
        if repository:

            template_path = os.path.join(__path__[0], "data", "templates", f"{repository['client_id']}.yaml")
            if os.path.exists(template_path):
                template = repository["client_id"]

            else:
                raise ValueError("Invalid template name")

    with open(template_path) as file:
        metadata = file.read()

    with open(manifest_path, "w") as file:
        file.write(
            f"{metadata}\ntemplate: {template}\n"
            f"files:\n  includes: []\n  excludes: []\n"
        )

    return dataset(path)


def notify(file: File, current_size: int, total_size: int = None, current_total_size: int = None) -> None:
    """Displays file transfer information.

    Args:
        file (File): File object.
        current_size (int): Current size of the file.
        total_size (int): Total size of the file (optional).
        current_total_size (int): Current total size of the transfer operation (optional).
    """
    if total_size:
        if current_size == file.size:
            print(f"{file.path}, {current_total_size}/{total_size}")
        else:
            print(
                f"{file.path}, {current_size}/{file.size}, {current_total_size}/{total_size}")
    else:
        print(f"{file.path}, {current_size}/{file.size}")


if __name__ == "__main__":
    # TODO: CLI implementation
    raise NotImplementedError
