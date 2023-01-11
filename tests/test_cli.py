import os
from string import Template

import yaml
import pytest

from typer.testing import CliRunner

import fairly
from fairly import LocalDataset

from cli import app
from cli.config import app as config_app
from cli.dataset import app as dataset_app

from .conftest import dummy_dataset
from tests import create_manifest_from_template, ROOT_DIR

runner = CliRunner()

# load environment variable token ii
FAIRLY_ZENODO_TOKEN_II = os.environ.get("FAIRLY_ZENODO_TOKEN_II")

# Here we define a fixed dataset that will be used by the tests bellow
CLIENT = fairly.client("zenodo")

def _test_commands(commands: list):
    for command in commands:
        result = runner.invoke(app, command)
        assert result.exit_code == 0, result.stdout

def test_show_config():
    result = runner.invoke(config_app, ["show"])
    assert result.exit_code == 0

@pytest.fixture(scope="module")
def dataset_clone_commands(dummy_dataset, templates):
    local_dataset = fairly.dataset(dummy_dataset.strpath)
    create_manifest_from_template(templates, "zenodo.yaml", local_dataset.path)
    remote_dataset = local_dataset.upload(CLIENT.client_id)

    return [
    # fairly dataset clone --url <url>
    ['dataset', 'clone', '--url', 'https://zenodo.org/record/1234567', 'tmp_1'],

    # fairly dataset clone --doi <doi>
    # TODO: method not implemented yet in fairly package
    # ['dataset', 'clone', '--doi', '10.5281/zenodo.1234567'],

    # fairly dataset clone --url <url> --token <token>
    ['dataset', 'clone', '--url', 'https://zenodo.org/record/7526539', '--token', FAIRLY_ZENODO_TOKEN_II, 'tmp_3'],

    # fairly dataset clone --repo <repo> --id <id>
    ['dataset', 'clone', '--repo', 'zenodo', '--id', remote_dataset.id, 'tmp_2'],
]

@pytest.mark.vcr(cassette_library_dir="./tests/fixtures/vcr_cassettes_cli")
def test_dataset_clone(dataset_clone_commands, bucket):
    '''Test the upload of a dataset by using its URL address, DOI or ID
    We test this with the same dummy dataset
    '''
    os.chdir(bucket.strpath)
    _test_commands(dataset_clone_commands)
    os.chdir(ROOT_DIR)

@pytest.mark.vcr(cassette_library_dir="./tests/fixtures/vcr_cassettes_cli",
                filter_headers=["authorization"], allow_playback_repeats=True)
def test_dataset_create(templates, dummy_dataset):
    '''The dataset creation with the cli simply means creating a manifest file
    in the directory that we want to be turn into a dataset'''
    
    # chdir to the dummy dataset otherwise the command will be executed in the src folder
    os.chdir(dummy_dataset.strpath)
    
    # Create a manifest file from the template in the current working directory
    runner.invoke(app, ["dataset", "create", "zenodo"])

    print(f"Working directory: {os.getcwd()}")
    # Create dummmy manifest file
    create_manifest_from_template(templates,"zenodo.yaml", dummy_dataset.strpath)

    #TODO: Check that all the files are added to the manifest
    
    # Reads the manifest file that makes the directory a dataset'
    dataset = fairly.dataset(dummy_dataset.strpath)
    assert dataset is not None
    assert isinstance(dataset, LocalDataset)

    # Should raise an exception if the manifest file already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(dataset_app, ["create", "zenodo"]), Exception) 
    
    # change to root directory
    os.chdir(ROOT_DIR)

@pytest.fixture(scope="module")
def dataset_upload_commands():
    return [
    ['dataset', 'upload', 'zenodo'],
    ['dataset', 'upload', '4tu'],
]

def test_dataset_upload(dataset_upload_commands, dummy_dataset):
    '''Test the upload of a dataset by using its URL address, DOI or ID
    We test this with the same dummy dataset
    '''
    os.chdir(dummy_dataset.strpath)
    
    # Classify the testing datasets so that they can be deleted without causing problems
    _test_commands(dataset_upload_commands)
    os.chdir(ROOT_DIR)


def test_delete_dataset():
    '''Test the deletion of datasets from the cli'''
    
    repos = ['zenodo', '4tu']
    
    for repo in repos:
        client = fairly.client(repo)
        datasets = client.get_account_datasets()
        for dataset in datasets:
            if dataset.metadata['title'] == 'My fairly test':
                runner.invoke(app, ['dataset', 'delete', '--repo', repo, '--url', dataset.url])
            else:
                raise Exception(f"Dataset {dataset.url} not found")




