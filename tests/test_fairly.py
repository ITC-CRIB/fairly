import json

import keyring
import pytest

import fairly
from fairly.client.figshare import FigshareClient
from fairly.client.invenio import InvenioClient
from fairly.dataset.local import LocalDataset
from fairly.dataset.remote import RemoteDataset
from tests.conftest import *

# Set testing flag
fairly.TESTING = True


def params_create_client():
    return [
        ("figshare", FigshareClient),
        ("invenio", InvenioClient)
    ]


def test_load_config():
    config = fairly.get_config("zenodo")
    assert config is not None
    assert config["url"] == "https://zenodo.org/"


def test_get_clients():
    clients = fairly.get_clients()
    assert clients
    assert "fairly" not in clients
    assert "figshare" in clients
    assert "invenio" in clients
    assert "djehuty" in clients



def test_save_config_stores_token_in_keychain(tmp_path, monkeypatch):
    """save_config must put the token in the keychain, never in config.json"""

    monkeypatch.setenv("HOME", str(tmp_path))

    token = "secret-token-value"
    client = fairly.client("figshare", token=token)
    assert client.config.get("token") == token

    client.save_config()

    id = client.repository_id or client.client_id

    assert keyring.get_password("fairly", id) == token

    config_path = tmp_path / ".fairly" / "config.json"
    with open(config_path) as file:
        data = json.load(file)
    assert "token" not in data.get(id, {})
    assert "token" not in json.dumps(data)

@pytest.mark.parametrize("client_id", list(fairly.get_clients()))
def test_init_resolves_token_from_keychain(client_id, tmp_path, monkeypatch):
    """Test Client.__init__ falls back to keychain when no kwargs/env var is provided."""

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv(f"FAIRLY_{client_id.upper()}_TOKEN", raising=False)

    keyring.set_password("fairly", client_id, "keychain-token-value")

    client = fairly.client(client_id)
    assert client.config.get("token") == "keychain-token-value"


def test_env_var_token_priority(tmp_path, monkeypatch):
    """Test FAIRLY_<ID>_TOKEN takes precedence over keychain."""

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("FAIRLY_FIGSHARE_TOKEN", "env-var-token-value")

    keyring.set_password("fairly", "figshare", "keychain-token-value")

    assert fairly.keychain.resolve_token("figshare") == "env-var-token-value"

    client = fairly.client("figshare")
    assert client.config.get("token") == "env-var-token-value"


@pytest.mark.parametrize("client_id", list(fairly.get_clients()))
def test_ingnore_legacy_plaintext_token(client_id, monkeypatch):
    """Test that a legacy plaintext token in config.json is never trusted/used."""

    monkeypatch.delenv(f"FAIRLY_{client_id.upper()}_TOKEN", raising=False)

    legacy_config = {
        "id": client_id,
        "client_id": client_id,
        "name": client_id,
        "url": "https://figshare.com/",
        "token": "legacy-plaintext-token"
    }
    monkeypatch.setattr(fairly, "get_repository", lambda uid: dict(legacy_config))

    client = fairly.client("figshare")
    assert not client.config.get("token")


@pytest.mark.parametrize("client_id, client_class", params_create_client())
def test_create_client(client_id, client_class):
    """Test client creation."""
    client = fairly.client(client_id)
    assert isinstance(client, client_class)
    assert client.client_id == client_id


@pytest.mark.parametrize("repository_id", fairly.get_repositories())
def test_dataset_upload_delete(repository_id, tmpdir):
    '''Test dataset upload to the recognized repositories.'''

    repository = fairly.get_repository(repository_id)
    if not repository.get("token"):
        pytest.skip("No access token")

    create_dummy_dataset(tmpdir)

    local_dataset = fairly.dataset(str(tmpdir))
    assert isinstance(local_dataset, LocalDataset)
    assert local_dataset.files is not None

    remote_dataset = local_dataset.upload(repository_id)
    assert isinstance(remote_dataset, RemoteDataset)
    assert len(remote_dataset.files) == len(local_dataset.files)

    remote_dataset.client.delete_dataset(remote_dataset.id)


@pytest.mark.parametrize("id", remote_dataset_ids())
def test_dataset_clone(id, tmpdir):
    '''Test the dataset cloning by using dataset URL address, DOI or ID.'''

    remote_dataset = fairly.dataset(id)
    assert isinstance(remote_dataset, RemoteDataset)

    local_dataset = remote_dataset.store(tmpdir)
    assert isinstance(local_dataset, LocalDataset)
    assert len(local_dataset.files) == len(remote_dataset.files)


@pytest.mark.parametrize("template", fairly.metadata_templates())
def test_dataset_create(template, tmpdir):
    '''Tests creation of a new dataset.'''

    dataset = fairly.init_dataset(str(tmpdir), template=template)
    assert isinstance(dataset, LocalDataset)
    assert dataset.template == template

    # Should raise an exception if dataset already exists
    with pytest.raises(Exception):
        assert isinstance(fairly.init_dataset(str(tmpdir)), Exception)


@pytest.mark.parametrize("repository_id", fairly.get_repositories())
def test_get_account_datasets(repository_id):

    repository = fairly.get_repository(repository_id)

    if not repository.get("token"):
        pytest.skip("No access token")

    client = fairly.client(repository_id)

    datasets = client.get_account_datasets()
    assert datasets is not None