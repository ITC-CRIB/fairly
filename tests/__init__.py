import os
import yaml
import json
import uuid
from dotenv import load_dotenv

load_dotenv()

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
    os.mkdir("tests/dummy_dataset")

    # Populate with dummy files
    with open("tests/dummy_dataset/test.txt", "w") as f:
        f.write("test")
except:
    print("Dataset already exists, skipping creation")


# for template_file in TEMPLATES:
# TODO: Maybe create a class for each metadata (this needs to change later with schemas)
def create_manifest_from_template(template_file) -> None:
    with open(f"./src/fairly/data/templates/{template_file}", "r") as f:
        template = f.read()
        template = yaml.safe_load(template)
        template['metadata']['title'] = ustring
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

    with open(f"./tests/dummy_dataset/manifest.yaml", "w") as f:
        f.write(yaml.dump(template))

# Generate 10 files with random names
if not os.path.exists("tests/dummy_dataset/data_files"):
    os.mkdir("tests/dummy_dataset/data_files")
    for i in range(10):
        with open(f"tests/dummy_dataset/data_files/{uuid.uuid4()}.txt", "w") as f:
            f.write("test")
else:
    # Check if there are 10 files in the directory
    if len(os.listdir("tests/dummy_dataset/data_files")) != 10:
        for i in range(10):
            with open(f"./tests/dummy_dataset/data_files/{uuid.uuid4()}.txt", "w") as f:
                f.write("test")
