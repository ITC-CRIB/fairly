import pytest

from ruamel.yaml import YAML
import dotenv

# Load environment variables
dotenv.load_dotenv()


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

    with open(path / "manifest.yaml", "w") as file:
        yaml.dump(manifest, file)

    for i in range(10):
        with open(path / f"file_{i}.txt", "w") as file:
            file.write(f"file_{i}")


def remote_dataset_ids():
    return [
        "https://zenodo.org/records/7759648",
        "10.5281/zenodo.7759648",
        "https://figshare.com/articles/dataset/_/12505823",
        "https://doi.org/10.6084/m9.figshare.12505823.v1",
    ]
