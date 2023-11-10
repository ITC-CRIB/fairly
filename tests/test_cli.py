import pytest
from tests.conftest import *

import fairly

import re

from cli import app

from typer.testing import CliRunner

runner = CliRunner()


def test_show_config():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0


@pytest.mark.parametrize("id", remote_dataset_ids())
def test_dataset_clone(id, tmpdir):
    '''Test dataset cloning by using dataset URL address, DOI or ID.'''

    result = runner.invoke(app, ["dataset", "clone", id, str(tmpdir)])
    assert result.exit_code == 0, result.stdout


@pytest.mark.parametrize("template", fairly.metadata_templates())
def test_dataset_create(template, tmpdir):
    '''Test dataset creation by using metadata templates.'''

    # Create a dummy dataset
    result = runner.invoke(app, ["dataset", "create", "--template", template, str(tmpdir)])
    assert result.exit_code == 0, result.stdout

    # Access the dummy dataset
    dataset = fairly.dataset(tmpdir)
    assert dataset.template == template

    # Should raise an exception if dataset already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(app, ["dataset", "create", tmpdir]), Exception)


@pytest.mark.parametrize("repository_id", fairly.get_repositories())
def test_dataset_upload_delete(repository_id, tmpdir):
    '''Test dataset upload to the recognized repositories.'''

    repository = fairly.get_repository(repository_id)
    if not repository.get("token"):
        pytest.skip("No access token")

    create_dummy_dataset(tmpdir)

    result = runner.invoke(app, ["dataset", "upload", str(tmpdir), repository_id])
    assert result.exit_code == 0, result.stdout

    match = "successfully uploaded" in result.stdout
    assert match

    url = match[0]

    result = runner.invoke(app, ["dataset", "delete", url])
    assert result.exit_code == 0, result.stdout
