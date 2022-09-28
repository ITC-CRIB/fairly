import fairly
import pytest
import os
import json

from tests import *

from fairly.client.figshare import FigshareClient
from fairly.client.zenodo import ZenodoClient

# We create a dummy dataset locally to upload and then download
# After we run al the tests the dataset is deleted from the repository
remote_dataset_id = None

def test_load_config():
    config = fairly.get_config("4tu")
    assert config is not None
    assert config["token"] == FIGSHARE_TOKEN


def test_get_clients():
    # except if client doesnt exist
    with pytest.raises(ValueError):
        fairly.client("4TU")

    clients = fairly.get_clients()
    assert clients
    assert "figshare" in clients
    assert "zenodo" in clients
    assert "djehuty" in clients

# Test clients creation
@pytest.mark.parametrize("client_id, token", [("fighsare", FIGSHARE_TOKEN), 
                            ("zenodo", ZENODO_TOKEN)])
def create_client():
    # Except if client doesnt exist
    with pytest.raises(ValueError):
        fairly.client("4TU")

    client = fairly.client(client_id, token)
    assert client._client_id == client_id

# Test the procedure of creating a local dataset and uploading it to
# the different remote repositories
figshare_client = fairly.client(id="figshare", token=FIGSHARE_TOKEN)
zenodo_client = fairly.client(id="zenodo", token=ZENODO_TOKEN)

@pytest.mark.parametrize("client, ustring", [(figshare_client, ustring),
                        (zenodo_client, ustring)])
def test_create_and_upload_dataset(client, ustring):
    # Test except if dummy dataset doesnt exist
    with pytest.raises(NotADirectoryError):
        local_dataset = fairly.dataset("./tests/non_existing_dataset")

    # This copies the template for the specific client 
    # and writes it to the dummy dataset directory
    create_manifest_from_template(f"{client.client_id}.yaml")

    local_dataset = fairly.dataset("./tests/dummy_dataset")
    assert local_dataset is not None
    assert local_dataset.metadata['title'] == ustring

    with pytest.raises(ValueError):
        tokenless_client = fairly.client(id='zenodo', token=None)
        local_dataset.upload(tokenless_client)

    remote_dataset = local_dataset.upload(client, notify=fairly.notify)
    assert remote_dataset is not None
    assert remote_dataset.metadata['title'] == ustring
    client._delete_dataset(remote_dataset.id)

@pytest.fixture
def create_remote_dataset():
    # Create remote dataset in figshare
    local_dataset = fairly.dataset("./tests/dummy_dataset")
    assert local_dataset is not None

    remote_dataset = local_dataset.upload("figshare")
    assert remote_dataset is not None
    assert remote_dataset.metadata['title'] == 'Test dataset'
    return remote_dataset    


def test_get_account_datasets():
    pass


def test_download():
    # Create remote dataset in figshare
    local_dataset = fairly.dataset("./tests/dummy_dataset")
    assert local_dataset is not None

    # TODO: fairly.set_dataset_repository(local_dataset, "figshare")

    # fourtu = fairly.client("4tu")
    # fairly.download("test", "test.txt", "tests/data/test.txt")


# CLEAN UP
# Write back the original config file
with open(os.path.expanduser("~/.fairly/config.json.bak"), "r") as f:
    config = json.load(f)
    with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
        json.dump(config, f)

# delete the backup
os.remove(os.path.expanduser("~/.fairly/config.json.bak"))
