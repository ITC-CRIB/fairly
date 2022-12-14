import os
import json
import dotenv

import pytest

# Load environment variables
dotenv.load_dotenv()
    
@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # Create user configuration directory if required
    if not os.path.exists(os.path.expanduser("~/.fairly")):
        try:
            os.makedirs(os.path.expanduser("~/.fairly"))
        except:
            print("Could not create ~/.fairly folder, check for permissions.")
            raise

    # Backup existing ~/.fairly/config.json
    try:
        with open(os.path.expanduser("~/.fairly/config.json"), "r") as f:
            config = json.load(f)
            with open(os.path.expanduser("~/.fairly/config.json.bak"), "w") as f:
                json.dump(config, f)

    except FileNotFoundError:
        print("No config file found, skipping backup.")

    # Create a test ~./fairly/config.json
    with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
        # Create configuration
        config = {
            "4tu": {"token": os.environ.get("FAIRLY_FIGSHARE_TOKEN")},
            "zenodo": {"token": os.environ.get("FAIRLY_ZENODO_TOKEN")},
        }
        f.write(json.dumps(config))

    request.addfinalizer(clean)


def clean():
    # Write back the original config file and delete backup if exists
    try:
        with open(os.path.expanduser("~/.fairly/config.json.bak"), "r") as file:
            config = json.load(file)
            with open(os.path.expanduser("~/.fairly/config.json"), "w") as file:
                json.dump(config, file)
        os.remove(os.path.expanduser("~/.fairly/config.json.bak"))

    except FileNotFoundError:
        pass


@pytest.fixture(scope="session")
def dummy_dataset(tmpdir_factory):
    """Create a dummy dataset for testing.

    Returns:
        Dummy dataset path
    """
    path = tmpdir_factory.mktemp("dummy_dataset")

    for i in range(10):
        with open(path / f"file_{i}.txt", "w") as file:
            file.write(f"file_{i}")

    return path
