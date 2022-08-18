import os

from  dotenv import load_dotenv
import pytest

import fairly


load_dotenv('./.env')
FIGSHARE_TOKEN = os.environ['FAIRLY_FIGSHARE_TOKEN']

def test_config():
    """
    Test the config file
    """
    with pytest.raises(TypeError) as e:
        fairly.client() # No id argument passed

    with pytest.raises(Exception) as e:
        client = fairly.client("komodo")
        assert "Invalid client id" in str(e.value)

    client = fairly.client("figshare", token=FIGSHARE_TOKEN)
    # assert client.config['token'] == FIGSHARE_TOKEN, "Token is not set"

    assert client.get_config()['token'] == FIGSHARE_TOKEN, "Token is not set"
    
    # Check that local global configuration
    assert os.path.exists("~/.fairly"), "~/fairly dir doesnt exsit"
    assert os.path.exists("~/.fairly/config.json"), "config.json doesnt exsit"

def test_working_with_metadata():
    pass

# Test that all instances of the client object work
def test_creating_datasets():    
    client = fairly.client("figshare", token=FIGSHARE_TOKEN)
    with pytest.raises(Exception) as e:
        client.create_dataset("")
        assert "Dataset name is not set" in str(e.value)
    with pytest.raises(Exception) as e:
        client.create_dataset("- /")
        assert "Dataset name is not set" in str(e.value)

    with pytest.raises(ValueError) as e:
        dataset = client.create_dataset({"name":"test_dataset"})
        assert 'Invalid metadata' in str(e.value)
    dataset = client.create_dataset({"title":"test_dataset"})
    assert dataset._id is not None, "Dataset id is not set"
    assert isinstance(dataset, fairly.dataset.remote.RemoteDataset), "Dataset is not instance of RemoteDataset"


def test_working_with_datasets():
    # test create new dataset

    # delete dataset

    # public dataset for testing
    # This should be in .env file 
    pass


def test_create_new_local_dataset():
    pass
    # dataset = fairly.Dataset("test_dataset")
    # assert dataset.name == "test_dataset", "Dataset name is not set"
    