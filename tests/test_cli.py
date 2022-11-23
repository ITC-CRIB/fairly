import os
import pytest
from pytest_mock import mocker

from typer.testing import CliRunner
import fairly
from fairly import LocalDataset

from cli import test_connection
from cli.repository import app as repo_app
from cli.dataset import app as dataset_app

runner = CliRunner()

def test_client_connection():
    '''Test the connection to the repository'''
    client = fairly.client(id="zenodo", token="1234")
    # Raise exception
    with pytest.raises(Exception):
        test_connection(client) 
    client = fairly.client("zenodo")
    assert test_connection(client) == True

def test_repository_list():
    result = runner.invoke(repo_app, ["list", "zenodo"])
    assert "zenodo" in result.stdout

def test_dataset_create(cli_testing_tempdir):
    '''The dataset creation with the cli simply means creatin a manifest file
    in the directory that wants to be turned into a dataset'''
    # Create a manifest file from the template in the current working directory
    runner.invoke(dataset_app, ["create", "zenodo"])

    # Create dummmy manifest file
    create_manifest_from_template("zenodo", cli_testing_tempdir)

    # Reads the manifest file that makes the directory a dataset'
    dataset = fairly.dataset(cli_testing.strpath)
    assert dataset is not None
    assert isinstance(dataset, LocalDataset)

    # Should raise an exception if the manifest file already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(dataset_app, ["create", "zenodo"]), Exception) 

    # remove the manifest file
    os.remove(f'{cli_testing}/manifest.yaml')

def test_dataset_upload():
    '''Test the upload of a dataset by using its URL address, DOI or ID'''
    # Test the connection to the repository by listing account datasets
    # Fetch the dataset metadata
    # stire the dataset metadata in the manifest
    pass

def test_dataset_download():
    '''Test the download of a dataset by using its URL address, DOI or ID'''
    # Test the connection to the repository by listing account datasets
    # Fetch the dataset metadata
    # stire the dataset metadata in the manifest

    # Upload dummy dataset to zenodo
    client = fairly.client("zenodo")
    # Create a dummy dataset
    dataset = fairly.dataset('./tests/fixtures/dummy_dataset')
    # Upload the dataset
    remote_dataset = dataset.upload(client.client_id, notify=fairly.notify)

    # Download using the id
    runner.invoke(dataset_app, ["download", "zenodo" , "--id", remote_dataset.id['id']]) 
    assert os.path.exists('./my_fairly_test') == True

    # Dataset could not be found
    # with pytest.raises(Exception):
    #     runner.invoke(dataset_app, ["download", "https://zenodo.org/record/123456"])
    
    

    pass