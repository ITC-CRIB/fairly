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

# Here we parametrize the test with different clients
@pytest.mark.parametrize("client_id, token", [("fighsare", FIGSHARE_TOKEN), 
                            "zenodo", ZENODO_TOKEN ] )
def create_client():
    client = fairly.client(client_id, token)
    assert client._client_id == client_id

# @pytest.fixture
# def figshare_client():
#     return fairly.client("figshare")

# @pytest.fixture
# def zenodo_client():
#     return fairly.client("zenodo")
figshare_client = fairly.client(id="figshare", token=FIGSHARE_TOKEN)
zenodo_client = fairly.client(id="zenodo", token=ZENODO_TOKEN)

def test_figshare_client(figshare_client):
    print(type(figshare_client))
    assert isinstance(figshare_client, FigshareClient)
    assert figshare_client.client_id == "figshare"

@pytest.mark.parametrize("client, ustring", [(figshare_client, ustring),
                        (zenodo_client, ustring)])
def test_create_and_upload_dataset(client, ustring):
    '''Here we create a simple dataset object based on a figshare 
    template and upload it to figshare'''
   
    # Test except if dummy dataset doesnt exist
    with pytest.raises(NotADirectoryError):
        local_dataset = fairly.dataset("./tests/non_existing_dataset")

    create_manifest_from_template(f"{client.client_id}.yaml")

    local_dataset = fairly.dataset("./tests/dummy_dataset")
    assert local_dataset is not None
    assert local_dataset.metadata['title'] == ustring

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
