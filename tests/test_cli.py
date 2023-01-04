import os
import pytest
# from pytest_mock import mocker
from tests import create_manifest_from_template


from typer.testing import CliRunner

import fairly
from fairly import LocalDataset

from cli import app
from cli.repository import app as repo_app
from cli.dataset import app as dataset_app

runner = CliRunner()

def test_repository_list():
    result = runner.invoke(repo_app, ["list", "zenodo"])
    assert "zenodo" in result.stdout

def test_dataset_create(cli_testing_tempdir):
    '''The dataset creation with the cli simply means creating a manifest file
    in the directory that wants to be turned into a dataset'''
    # Create a manifest file from the template in the current working directory
    runner.invoke(app, ["dataset", "create", "zenodo"])

    print(f"Working directory: {os.getcwd()}")
    # Create dummmy manifest file
    create_manifest_from_template("../src/fairly/data/templates/","zenodo.yaml", cli_testing_tempdir)

    # Reads the manifest file that makes the directory a dataset'
    dataset = fairly.dataset(cli_testing_tempdir.strpath)
    assert dataset is not None
    assert isinstance(dataset, LocalDataset)

    # Should raise an exception if the manifest file already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(dataset_app, ["create", "zenodo"]), Exception) 

    # remove the manifest file
    os.remove(f'{cli_testing_tempdir.strpath}/manifest.yaml')

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

# Here we define a fixed dataset that will be used by the tests bellow
CLIENT = fairly.client("zenodo")
DATASET = fairly.dataset('./tests/fixtures/dummy_dataset')
REMOTE_DATASET = DATASET.upload(CLIENT.client_id, notify=fairly.notify)

DATASET_COMMANDS = [
    # fairly dataset clone --url <url>
    ['dataset', 'clone', '--url', 'https://zenodo.org/record/1234567', 'tmp_1'],

    # fairly dataset clone --doi <doi>
    # TODO: method not implemented yet in fairly package
    # ['dataset', 'clone', '--doi', '10.5281/zenodo.1234567'],

    # fairly dataset clone --repo <repo> --id <id>
    ['dataset', 'clone', '--repo', 'zenodo', '--id', REMOTE_DATASET.id['id'], 'tmp_2'], 
]

@pytest.mark.vcr(cassette_library_dir="tests/fixtures/vcr_cassettes_cli",
                filter_headers=["authorization"], allow_playback_repeats=True)
@pytest.mark.parametrize('command', DATASET_COMMANDS)
def test_cli_dataset_clone(command: list, cli_testing_tempdir):
    '''Test the download of a dataset by using its URL address, DOI or ID'''
    working_dir = os.getcwd()
    print(command)
    # fairly dataset clone --url <url>
    os.chdir(cli_testing_tempdir.strpath)
    result = runner.invoke(app, command)
    # for positive download operations is good enough to check that the command
    # was executed without errors
    assert result.exit_code == 0
    
    # go back to the original working directory
    os.chdir(working_dir)