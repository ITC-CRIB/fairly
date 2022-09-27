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
def create_manifest_from_template(template_file) -> None:
    with open(f"./src/fairly/data/templates/{template_file}", "r") as f:
        template = f.read()
        template = yaml.safe_load(template)
        template['metadata']['title'] = ustring
        template['metadata']['authors'] = [ ustring ]
        
        # Required fields for zenodo
        template['metadata']['description'] = ustring
        template['metadata']['license'] = 'cc-by-nc-4.0'

    with open(f"./tests/dummy_dataset/manifest.yaml", "w") as f:
        f.write(yaml.dump(template))

