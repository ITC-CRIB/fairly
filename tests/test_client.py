import os

from  dotenv import load_dotenv
import pytest

import fairly


load_dotenv('./.env')
FIGSHARE_TOKEN = os.environ['FAIRLY_FIGSHARE_TOKEN']
DUMMY_DATASET = "./tests/dummy_dataset/"

def test_config():
    """
    Test the config file
    """
    import fairly

    config_dir = os.path.expanduser("~/.fairly/")
    config_file = os.path.join(config_dir, "config.json")

    # Check that local global configuration is set when fairly is imported
    assert os.path.exists(config_dir), "~/fairly dir doesnt exist"
    assert os.path.exists(config_file), "config.json doesnt exist"

    # delete ~/.fairly/ directory and its contents
    for file_name in os.listdir(config_dir):
        file_path = os.path.join(config_dir, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    os.rmdir(config_dir)


def test_create_client():
    with pytest.raises(TypeError) as e:
        fairly.client() # No id argument passed

    with pytest.raises(Exception) as e:
        client = fairly.client("komodo")
        assert "Invalid client id" in str(e.value)
    
    client = fairly.client("figshare", token=FIGSHARE_TOKEN)
    # assert client.config['token'] == FIGSHARE_TOKEN, "Token is not set"

    assert client.get_config()['token'] == FIGSHARE_TOKEN, "Token is not set"


def test_create_new_local_dataset():
    # Create metadata associated to the target repository
    # The dataset is created in the local directory
    dataset = fairly.dataset.local.LocalDataset(DUMMY_DATASET)
    
    # Upload data to target dataset

    pass

# Test that all instances of the client object work
def test_datasets():    
    client = fairly.client("figshare", token=FIGSHARE_TOKEN)

    # Empty dataset should raise an error
    with pytest.raises(Exception) as e:
        client.create_dataset("")
        assert "Dataset name is not set" in str(e.value)

    # Dataset name should be a string of literal characters
    with pytest.raises(Exception) as e:
        client.create_dataset("- /")
        assert "Dataset name is not set" in str(e.value)

    # Dataset dont have name but titles and ids
    with pytest.raises(ValueError) as e:
        dataset = client.create_dataset({"name":"test_dataset"})
        assert 'Invalid metadata' in str(e.value)

    # Dataset is only created if title is passed
    dataset = client.create_dataset({"title":"test_dataset"})
    
    assert dataset._id is not None, "Dataset id is not set"
    assert isinstance(dataset, fairly.dataset.remote.RemoteDataset), "Dataset is not instance of RemoteDataset"

def test_account_datasets():
    # Get account datasets
    client = fairly.client("figshare", token=FIGSHARE_TOKEN)
    account_datasets = client.get_account_datasets()
    assert len(account_datasets) > 0, "No datasets found"

def test_download_dataset():
    # Download dataset
    pass

def test_uploading_files():
    # Upload files to dataset
    pass

def test_working_with_datasets():
    # test create new dataset

    # delete dataset

    # public dataset for testing
    # This should be in .env file 
    pass



    