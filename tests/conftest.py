import os.path

import dotenv
import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from ruamel.yaml import YAML

# Load environment variables
dotenv.load_dotenv()


class InMemoryKeyring(KeyringBackend):
    """Simple keyring backend for tests, independent of keyring extras."""

    priority = 1

    def __init__(self):
        self._store = {}

    def get_password(self, service, username):
        return self._store.get((service, username))

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def delete_password(self, service, username):
        key = (service, username)
        if key not in self._store:
            raise PasswordDeleteError("No such credential")
        del self._store[key]

@pytest.fixture(autouse=True)
def set_keyring():
    """Set keyring for testing."""

    keyring.set_keyring(InMemoryKeyring())

def create_dummy_dataset(path):
    """Create a dummy dataset for testing.

    Returns:
        Dummy dataset path
    """
    manifest = {
        "metadata": {
            "title": "Title",
            "description": "Description",
            "authors": ["Surname, Name"],
            "license": "MIT",
            "type": "dataset",
            "access_type": "open"
        },
        "files": {
            "includes": ["*.txt"],
            "excludes": []
        }
    }

    yaml = YAML()

    with open(os.path.join(path, "manifest.yaml"), "w") as file:
        yaml.dump(manifest, file)

    for i in range(10):
        with open(os.path.join(path, f"file_{i}.txt"), "w") as file:
            file.write(f"file_{i}")


def remote_dataset_ids():
    return [
        "https://zenodo.org/records/7759648",
        "10.5281/zenodo.7759648",
        "https://figshare.com/articles/dataset/_/12505823",
        "https://doi.org/10.6084/m9.figshare.12505823.v1",
        "https://data.4tu.nl/datasets/8c9cf432-a4cf-4ba4-aaf5-92b1a99ca20b",
        "10.4121/13697596.v1",
        # "https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/M9JGU2",  # TOOD: Forbiden error on Datasvers.
        # "10.34894/M9JGU2",
    ]
