import os
import pytest
# from pytest_mock import mocker
from tests import create_manifest_from_template


from typer.testing import CliRunner

import fairly
from fairly import LocalDataset

from cli.main import app
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
    runner.invoke(dataset_app, ["create", "zenodo"])

    # Create dummmy manifest file
    create_manifest_from_template("zenodo.yaml", cli_testing_tempdir)

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

# vcr decorator
@pytest.mark.vcr(cassette_library_dir="tests/fixtures/vcr_cassettes_cli",
                filter_headers=["authorization"])
def test_dataset_download():
    '''Test the download of a dataset by using its URL address, DOI or ID'''
    # A private function to test that all commands are working
    def _check_download(dataset_path, remote):
        assert os.path.exists(dataset_path) == True
        assert os.path.exists(f'{dataset_path}/manifest.yaml') == True
        dataset = fairly.dataset(dataset_path)
        assert dataset is not None
        assert isinstance(dataset, LocalDataset)
        if remote: assert len(remote.files) == len(dataset.files)

        # remove files in the directory
        for file in os.listdir(dataset_path):
            os.remove(f'{dataset_path}/{file}')
        os.rmdir(dataset_path)

    client = fairly.client("zenodo")
    
    # Create a dummy dataset
    dataset = fairly.dataset('./tests/fixtures/dummy_dataset')
    
    # Upload the dataset
    remote_dataset = dataset.upload(client.client_id, notify=fairly.notify)
    assert remote_dataset is not None
    assert len(remote_dataset.files) == len(dataset.files)

    # fairly dataset clone <url|doi>
    runner.invoke(app, ["dataset", "clone", "--doi", "10.5281/zenodo.3929547"])
    _check_download()

    # runner.invoke(app, ["dataset", "clone", "--url", remote_dataset.url])
    # _check_download()

    # fairly dataset clone --repo zenodo --id 6026285
    runner.invoke(app, ["dataset", "clone", "--repo", "zenodo" , "--id", remote_dataset.id['id']]) 
    _check_download()
