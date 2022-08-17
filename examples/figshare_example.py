import sys
from distutils.command.config import config

import yaml
from  dotenv import load_dotenv
import os
from pprint import *

import fairly


load_dotenv('./.env')

if __name__ == "__main__":
    # Argv is the token to use
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.environ['FOURTU_TOKEN']

    # Get the client
    client = fairly.client(id="figshare", token=token)
    account_datasets = client.get_account_datasets()
    first_dataset = account_datasets[0]

    # write the serialized data set into a file
    with open('./examples/figshare_dataset.yaml', 'w') as f:
        yaml.dump(first_dataset.serialize(), f)
    
    # write client configuration to a file
    with open('./examples/config.yaml', 'w') as f:
        yaml.dump(client.get_config())




