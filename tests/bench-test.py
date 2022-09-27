import fairly
import os
from dotenv import load_dotenv

load_dotenv()


# Load environment 

FIGSHARE_TOKEN = os.environ.get("FAIRLY_FIGSHARE_TOKEN")

clients = fairly.get_clients()

config = fairly.get_config("4tu")

local_dataset = fairly.dataset("./tests/dummy_dataset")

fourtu = fairly.client(id='figshare', token=config['token'] )

my_datasets = fourtu.get_account_datasets()
