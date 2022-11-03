import os
import json
import re
import pytest
import shutil

import fairly
from tests import *

from fairly.dataset import Dataset

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
@pytest.mark.parametrize("client_id, token, client_class", [("figshare", FIGSHARE_TOKEN), 
                            ("zenodo", ZENODO_TOKEN)])
def create_client():    
    # Except if client doesnt exist
    with pytest.raises(ValueError):
        fairly.client("4TU")

    client = fairly.client(client_id, token)
    assert isinstance(client, client_class)
    assert client._client_id == client_id


# SET UP CLIENTS TO RUN CREATE, UPLOAD, DOWNLOAD, DELETE DATASETS
figshare_client = fairly.client(id="figshare", token=FIGSHARE_TOKEN)
zenodo_client = fairly.client(id="zenodo", token=ZENODO_TOKEN)

# Test the procedure of creating a local dataset and uploading it to
# the different remote repositories
@pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", [(figshare_client),
                        (zenodo_client)])
def test_create_and_upload_dataset(client: fairly.Client):
    # Test except if dummy dataset doesnt exist
    with pytest.raises(NotADirectoryError):
        local_dataset = fairly.dataset("./tests/non_existing_dataset")

    # This copies the template for the specific client 
    # and writes it to the dummy dataset directory
    create_manifest_from_template(f"{client.client_id}.yaml")

    local_dataset = fairly.dataset("./tests/fixtures/dummy_dataset")
    assert local_dataset is not None
    assert local_dataset.metadata['title'] == "My fairly test"
    assert local_dataset.files is not None

    # # Notify user that token is not set
    with pytest.raises(ValueError):
        tokenless_client = fairly.client(id='zenodo', token=None)
        local_dataset.upload(tokenless_client)

    remote_dataset = local_dataset.upload(client.client_id, notify=fairly.notify)
    assert remote_dataset is not None
    assert remote_dataset.metadata['title'] == "My fairly test"
    assert remote_dataset.files is not None
    assert len(remote_dataset.files) == 10
    client._delete_dataset(remote_dataset.id)
    dirs = [d for d in os.listdir('./tests/') if re.match(r'[a-z]*\.dataset', d)]
    for dir in dirs:
        shutil.rmtree(f"./tests/{dir}/")


# Test the download of the different datasets created
@pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", [(figshare_client),
                        (zenodo_client)])
def test_download_dataset(client):
    # local dataset is created in the tests folder
    # and then deleted after the test is done
    create_manifest_from_template(f"{client.client_id}.yaml")

    local_dataset = fairly.dataset("./tests/fixtures/dummy_dataset")

    remote_dataset = local_dataset.upload(client, notify=fairly.notify)
    assert remote_dataset is not None

    # Raise error if folder to store the dataset is not empty
    with pytest.raises(ValueError):
        remote_dataset.store("./tests/fixtures/dummy_dataset")

    remote_dataset.store(f"./tests/{client.client_id}.dataset")
    # load the dataset from the file
    local_dataset = fairly.dataset(f"./tests/{client.client_id}.dataset")
    
    assert isinstance(local_dataset, Dataset)
    assert len(local_dataset.files) == 10
    
    # delete the dataset from the remote repository
    client._delete_dataset(remote_dataset.id)
    dirs = [d for d in os.listdir('./tests/') if re.match(r'[a-z]*\.dataset', d)]
    for dir in dirs:
        shutil.rmtree(f"./tests/{dir}/")

@pytest.mark.vcr(cassette_library_dir='tests/fixtures/vcr_cassettes', filter_headers=['authorization'])
@pytest.mark.parametrize("client", [(figshare_client),
                        (zenodo_client)])
def test_get_account_datasets(client):
    # get all datasets from the account
    datasets = client.get_account_datasets()
    assert datasets is not None    

# CLEAN UP
# Write back the original config file
with open(os.path.expanduser("~/.fairly/config.json.backup"), "r") as f:
    config = json.load(f)
    with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
        json.dump(config, f)

assert os.path.exists(os.path.expanduser("~/.fairly/config.json.backup"))

# @pytest.fixture(scope='session', autouse=True)
# def run_after_tests():
#     # delete the backup
#     os.remove(os.path.expanduser("~/.fairly/config.json.backup"))
#     assert not os.path.exists(os.path.expanduser("~/.fairly/config.json.backup"))
#     os.remove("./tests/fixtures/dummy_dataset/manifest.yaml")
#     assert not os.path.exists("./tests/fixtures/dummy_dataset/manifest.yaml")




