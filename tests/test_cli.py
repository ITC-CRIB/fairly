import os
from string import Template

import pytest
from .conftest import dummy_dataset


from typer.testing import CliRunner

import fairly
from fairly import LocalDataset

from cli import app
from cli.repository import app as repo_app
from cli.dataset import app as dataset_app

runner = CliRunner()

# Here we define a fixed dataset that will be used by the tests bellow
CLIENT = fairly.client("zenodo")

@pytest.fixture(scope="module")
def DATASET_COMMANDS(dummy_dataset):
    local_dataset = fairly.dataset(dummy_dataset.strpath)
    remote_dataset = local_dataset.upload(CLIENT.client_id)

    return [
    # fairly dataset clone --url <url>
    ['dataset', 'clone', '--url', 'https://zenodo.org/record/1234567', 'tmp_1'],

    # fairly dataset clone --doi <doi>
    # TODO: method not implemented yet in fairly package
    # ['dataset', 'clone', '--doi', '10.5281/zenodo.1234567'],

    # fairly dataset clone --repo <repo> --id <id>
    ['dataset', 'clone', '--repo', 'zenodo', '--id', remote_dataset.id, 'tmp_2'],
]

def test_repository_list():
    result = runner.invoke(repo_app, ["list", "zenodo"])
    assert "zenodo" in result.stdout

@pytest.mark.vcr(cassette_library_dir="tests/fixtures/vcr_cassettes_cli",
                filter_headers=["authorization"], allow_playback_repeats=True)
def test_dataset_create(templates, dummy_dataset):
    '''The dataset creation with the cli simply means creating a manifest file
    in the directory that wants to be turned into a dataset'''
    
    # chdir to the dummy dataset otherwise the command will be executed in the src folder
    os.chdir(dummy_dataset.strpath)
    
    # Create a manifest file from the template in the current working directory
    runner.invoke(app, ["dataset", "create", "zenodo"])

    print(f"Working directory: {os.getcwd()}")
    # Create dummmy manifest file
    create_manifest_from_template(templates,"zenodo.yaml", dummy_dataset.strpath)

    # Reads the manifest file that makes the directory a dataset'
    dataset = fairly.dataset(dummy_dataset.strpath)
    assert dataset is not None
    assert isinstance(dataset, LocalDataset)

    # Should raise an exception if the manifest file already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(dataset_app, ["create", "zenodo"]), Exception) 

def test_dataset_upload():
    '''Test the upload of a dataset by using its URL address, DOI or ID
    We test this with the same dummy dataset
    '''
    # Test the connection to the repository by listing account datasets
    # Fetch the dataset metadata
    # stire the dataset metadata in the manifest
    pass

def gen_dataset_path(dataset):
    '''Generates a path name for a dataset directory in the current working directory
    based on the title of the dataset
    '''
    return dataset.metadata['title'].replace(' ', '_')




