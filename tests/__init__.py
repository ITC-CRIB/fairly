import os
import yaml
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

import vcr

import pytest
import fairly

# Requires develop to have .env file with FAIRLY_FIGSHARE_TOKEN
FIGSHARE_TOKEN = os.environ.get("FAIRLY_FIGSHARE_TOKEN")
ZENODO_TOKEN = os.environ.get("FAIRLY_ZENODO_TOKEN")

# load clients from supported clients
TEMPLATES = os.listdir("./src/fairly/data/templates")

# We generate a unique string that we can use to populate metadata for testing
ustring = str(uuid.uuid4())

# Create a file in ~./fairly/config.json
with open(os.path.expanduser("~/.fairly/config.json"), "w") as f:
    # Create dict with config
    config = { "4tu": { "token": FIGSHARE_TOKEN }, 
               "zenodo": { "token": ZENODO_TOKEN } 
             }
    f.write(json.dumps(config))

# copy existing ~/.fairly/config.json to ~/.fairly/config.json.bak
# We do this to test the config file creation and loading
try: 
    with open(os.path.expanduser("~/.fairly/config.json"), "r") as f:
        config = json.load(f)
        with open(os.path.expanduser("~/.fairly/config.json.bak"), "w") as f:
            json.dump(config, f)
except FileNotFoundError:
    print("No config file found, skipping backup")

# Create a dummy dataset
try:
    os.mkdir("tests/fixtures/dummy_dataset")

    # Populate with dummy files
    with open("tests/fixtures/dummy_dataset/test.txt", "w") as f:
        f.write("test")
except:
    print("Dataset already exists, skipping creation")


def create_manifest_from_template(template_file: str, path) -> None:
    """Create a manifest file from a template file
    Parameters
    ----------
    template_file : str
        Name of the template file in yaml format e.g. figshare.yaml
        the file is extracted from the templates folder
    """
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

    with open(f"{path}/manifest.yaml", "w") as f:
        f.write(yaml.dump(template))

# Set testing flag
fairly.TESTING = True


