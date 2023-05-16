import os
from ruamel.yaml import YAML
import yaml
import shutil
from functools import lru_cache

import pytest
# FIXME: Patches used by vcrpy is not compatible with the latest urllib3
# import vcr

import fairly
from fairly.dataset import Dataset
from fairly.client.figshare import FigshareClient
from fairly.client.zenodo import ZenodoClient

# We generate a string that we can use to populate metadata for testing
dummy_string = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Set testing flag
fairly.TESTING = True
ROOT_DIR = os.getcwd()



@lru_cache(maxsize=None)
def params_clients():
    return [
        fairly.client(id="figshare", token=os.environ.get("FAIRLY_FIGSHARE_TOKEN")),
        fairly.client(id="zenodo", token=os.environ.get("FAIRLY_ZENODO_TOKEN"))
    ]


@lru_cache(maxsize=None)
def params_create_client():
    return [
        ("figshare", FigshareClient),
        ("zenodo", ZenodoClient)
    ]


def create_manifest_from_template(template_path: str, template_file: str,  target_path) -> None:
    """Create a manifest file from a template file
    Parameters
    ----------
    template_path : str
        Path

    template_file : str
        Name of the template file in yaml format e.g. figshare.yaml
        the file is extracted from the templates folder

    target_path : str
        Path to the target folder where the manifest file will be created

    Example
    -------
    >>> create_manifest_from_template("./src/fairly/data/templates/", "figshare.yaml", "./tests/data/")
    """
    with open(f"{template_path}/{template_file}", "r") as f:
        template = f.read()
        template = yaml.safe_load(template)
        template['metadata']['title'] = "My fairly test"
        template['metadata']['description'] = dummy_string
        # Add files key to the manifest so that files are added to the dataset object
        template['files'] = { 'excludes': [], 'includes': ["*.txt"] }
        if template_file == "figshare.yaml":
            template['metadata']['authors'] = [ dummy_string ]
        if template_file == "zenodo.yaml":
            template['metadata']['creators'] = [ { "name": dummy_string } ]
            template['metadata']['authors'] = [ {"name" : dummy_string } ]
            template['metadata']['description'] = dummy_string
            template['metadata']['license'] = 'cc-by-nc-4.0'
            template['metadata']['type'] = 'dataset'
            # template dates
            template['metadata']['publication_date'] = '2020-01-01'

    with open(f"{target_path}/manifest.yaml", "w") as f:
        f.write(yaml.dump(template))


def test_load_config():
    config = fairly.get_config("zenodo")
    assert config is not None
    assert config["url"] == "https://zenodo.org/"


def test_get_clients():
    clients = fairly.get_clients()
    assert clients
    assert "fairly" not in clients
    assert "figshare" in clients
    assert "zenodo" in clients
    assert "djehuty" in clients


@pytest.mark.parametrize("client_id, client_class", params_create_client())
def test_create_client(client_id, client_class):
    """Test client creation."""
    client = fairly.client(client_id)
    assert isinstance(client, client_class)
    assert client.client_id == client_id


# FIXME: Patches used by vcrpy is not compatible with the latest urllib3
# @pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", params_clients())
def test_create_and_upload_dataset(templates, client: fairly.Client, dummy_dataset):
    """
    Test the procedure of creating a local dataset and uploading it to various
    remote repositories.
    """
    # Test exception if dummy dataset does not exist
    with pytest.raises(NotADirectoryError):
        local_dataset = fairly.dataset("./tests/non_existing_dataset")

    # This copies the template for the specific client
    # and writes it to the dummy dataset directory
    create_manifest_from_template(templates, f"{client.client_id}.yaml", dummy_dataset)

    local_dataset = fairly.dataset(dummy_dataset)
    assert local_dataset is not None
    assert local_dataset.metadata['title'] == "My fairly test"
    assert local_dataset.files is not None

    # Notify user that token is not set
    with pytest.raises(ValueError):
        tokenless_client = fairly.client(client.client_id)
        local_dataset.upload(tokenless_client)

    remote_dataset = local_dataset.upload(client, notify=fairly.notify)
    assert remote_dataset is not None
    assert remote_dataset.metadata['title'] == "My fairly test"
    assert remote_dataset.files is not None
    assert len(remote_dataset.files) == 10
    client._delete_dataset(remote_dataset.id)


# FIXME: Patches used by vcrpy is not compatible with the latest urllib3
# @pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", params_clients())
def test_download_dataset(templates, client: fairly.Client, dummy_dataset):
    """Test the download of the different datasets created."""
    # Local dataset is created in the tests folder
    # and then deleted after the test is done
    create_manifest_from_template(templates, f"{client.client_id}.yaml", dummy_dataset)

    local_dataset = fairly.dataset(dummy_dataset)

    remote_dataset = local_dataset.upload(client, notify=fairly.notify)
    assert remote_dataset is not None

    # Raise error if folder to store the dataset is not empty
    with pytest.raises(ValueError):
        remote_dataset.store(dummy_dataset)

    local_path = f"{dummy_dataset}/{client.client_id}.dataset"

    local_dataset = remote_dataset.store(local_path)
    assert isinstance(local_dataset, Dataset)
    assert len(local_dataset.files) == 10

    local_dataset = fairly.dataset(local_path)
    assert len(local_dataset.files) == 10

    # Delete the dataset from the remote repository
    client._delete_dataset(remote_dataset.id)

    # Delete the local dataset
    shutil.rmtree(local_path)


# FIXME: Patches used by vcrpy is not compatible with the latest urllib3
# @pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", params_clients())
def test_get_account_datasets(client: fairly.Client):
    # Get all datasets from the account
    datasets = client.get_account_datasets()
    assert datasets is not None