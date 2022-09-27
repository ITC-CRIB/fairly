import fairly
import pytest
import os
import json

from dotenv import load_dotenv

load_dotenv()

# copy existing ~/.fairly/config.json to ~/.fairly/config.json.bak
# We do this to test the config file creation and loading
try: 
    with open(os.path.expanduser("~/.fairly/config.json"), "r") as f:
        config = json.load(f)
        with open(os.path.expanduser("~/.fairly/config.json.bak"), "w") as f:
            json.dump(config, f)
except FileNotFoundError:
    print("No config file found, skipping backup")

# Requires develop to have .env file with FAIRLY_FIGSHARE_TOKEN
FIGSHARE_TOKEN = os.environ.get("FAIRLY_FIGSHARE_TOKEN")

# Create a file in ~./fairly/config.json
with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
    # Create dict with config
    config = { "4tu": { "token": FIGSHARE_TOKEN } }
    f.write(json.dumps(config))

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

def test_get_datasets():
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