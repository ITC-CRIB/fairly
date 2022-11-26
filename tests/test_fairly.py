import os
import json
import yaml
import re
import pytest
import shutil
import uuid
import vcr

from dotenv import load_dotenv

import fairly

from fairly.dataset import Dataset

# Set testing flag
fairly.TESTING = True

load_dotenv()

# Requires develop to have .env file with FAIRLY_FIGSHARE_TOKEN
FIGSHARE_TOKEN = os.environ.get("FAIRLY_FIGSHARE_TOKEN")
ZENODO_TOKEN = os.environ.get("FAIRLY_ZENODO_TOKEN")

# SET UP CLIENTS TO RUN CREATE, UPLOAD, DOWNLOAD, DELETE DATASETS
figshare_client = fairly.client(id="figshare", token=FIGSHARE_TOKEN)
zenodo_client = fairly.client(id="zenodo", token=ZENODO_TOKEN)


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # Backup existing ~/.fairly/config.json
    try:
        with open(os.path.expanduser("~/.fairly/config.json"), "r") as f:
            config = json.load(f)
            with open(os.path.expanduser("~/.fairly/config.json.bak"), "w") as f:
                json.dump(config, f)
    except FileNotFoundError:
        print("No config file found, skipping backup")

    # Create a test ~./fairly/config.json
    with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
        # Create dict with config
        config = { "4tu": { "token": FIGSHARE_TOKEN },
                   "zenodo": { "token": ZENODO_TOKEN }
                 }
        f.write(json.dumps(config))

    # Create a dummy dataset
    try:
        os.mkdir("tests/fixtures/dummy_dataset")

        # Populate with dummy files
        with open("tests/fixtures/dummy_dataset/test.txt", "w") as f:
            f.write("test")
    except:
        print("Dataset already exists, skipping creation")

    request.addfinalizer(clean)


def clean():
    # Write back the original config file
    with open(os.path.expanduser("~/.fairly/config.json.bak"), "r") as f:
        config = json.load(f)
        with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
            json.dump(config, f)

    # delete the backup
    os.remove(os.path.expanduser("~/.fairly/config.json.bak"))


# TODO: Maybe create a class for each metadata (this needs to change later with schemas)
def create_manifest_from_template(template_file: str) -> None:
    """Create a manifest file from a template file
    Parameters
    ----------
    template_file : str
        Name of the template file in yaml format e.g. figshare.yaml
        the file is extracted from the templates folder
    """
    # We generate a unique string that we can use to populate metadata for testing
    ustring = str(uuid.uuid4())

    with open(f"./src/fairly/data/templates/{template_file}", "r") as f:
        template = f.read()
        template = yaml.safe_load(template)
        template['metadata']['title'] = "My fairly test"
        template['metadata']['description'] = ustring
        # Add files key to the manifest so that files are added to the dataset object
        template['files'] = { 'excludes': [], 'includes': ["*.txt"] }
        if template_file == "figshare.yaml":
            template['metadata']['authors'] = [ ustring ]
        if template_file == "zenodo.yaml":
            template['metadata']['creators'] = [ { "name": ustring } ]
            template['metadata']['authors'] = [ {"name" : ustring } ]
            template['metadata']['description'] = ustring
            template['metadata']['license'] = 'cc-by-nc-4.0'
            template['metadata']['type'] = 'dataset'
            # template dates
            template['metadata']['publication_date'] = '2020-01-01'

    with open(f"./tests/fixtures/dummy_dataset/manifest.yaml", "w") as f:
        f.write(yaml.dump(template))


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

    remote_dataset = local_dataset.upload(client, notify=fairly.notify)
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
