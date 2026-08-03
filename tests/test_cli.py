import re
import subprocess

import keyring
import pytest
from click.testing import CliRunner

import fairly
from fairly.cli import cli
from tests.conftest import *


def test_help():
    """Test if CLI is reachable from the system terminal."""
    exit_status = subprocess.call(["fairly", "--help"])
    assert exit_status == 0

def test_cli_config_masks_token(monkeypatch):
    """Test `repository config` command shows a 6-character masked token, never the full token."""

    monkeypatch.delenv("FAIRLY_FIGSHARE_TOKEN", raising=False)
    token = "abcdef1234567890SECRETTAIL"
    keyring.set_password("fairly", "figshare", token)

    runner = CliRunner()
    result = runner.invoke(cli, ["repository", "config", "figshare"])
    assert result.exit_code == 0, result.stdout

    assert "abcdef..." in result.stdout
    assert token not in result.stdout
    assert "SECRETTAIL" not in result.stdout


def test_cli_config_shows_not_set(monkeypatch):
    """Test `repository config` command shows '(not set)' when no token is found."""

    monkeypatch.delenv("FAIRLY_ZENODO_TOKEN", raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["repository", "config", "zenodo"])
    assert result.exit_code == 0, result.stdout
    assert "(not set)" in result.stdout


def test_cli_config_ignores_stale_plaintext_token(monkeypatch):
    """Tests that `repository config` command ignores a stale plaintext token in config.json and shows '(not set)' instead."""

    monkeypatch.delenv("FAIRLY_FIGSHARE_TOKEN", raising=False)

    stale = {
        "id": "figshare",
        "client_id": "figshare",
        "name": "Figshare",
        "url": "https://figshare.com/",
        "api_url": "https://api.figshare.com/v2/",
        "token": "stale-plaintext-token",
    }
    monkeypatch.setattr(fairly, "get_repository", lambda uid: dict(stale))

    runner = CliRunner()
    result = runner.invoke(cli, ["repository", "config", "figshare"])
    assert result.exit_code == 0, result.stdout
    assert "(not set)" in result.stdout
    assert "stale-plaintext-token" not in result.stdout


@pytest.mark.parametrize("id", remote_dataset_ids())
def test_dataset_clone(id, tmpdir):
    """Test dataset cloning by using dataset URL address, DOI or ID."""
    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "clone", "--id", id, "--path", str(tmpdir)])
    assert result.exit_code == 0, result.stdout


@pytest.mark.parametrize("template", fairly.metadata_templates())
def test_dataset_init(template, tmpdir):
    """Test dataset creation by using metadata templates."""
    runner = CliRunner()
    # Create a dummy dataset
    result = runner.invoke(cli, ["dataset", "init", "--template", template, "--path", str(tmpdir)])
    assert result.exit_code == 0, result.stdout

    # Access the dummy dataset
    dataset = fairly.dataset(tmpdir)
    assert dataset.template == template

    # Should raise an exception if dataset already exists
    with pytest.raises(Exception):
        assert isinstance(runner.invoke(cli, ["dataset", "create", tmpdir]), Exception)


@pytest.mark.parametrize("repository_id", fairly.get_repositories())
def test_dataset_upload_delete(repository_id, tmpdir):
    """Test dataset upload to the recognized repositories."""
    runner = CliRunner()
    repository = fairly.get_repository(repository_id)
    if not repository.get("token"):
        pytest.skip("No access token")

    create_dummy_dataset(tmpdir)

    result = runner.invoke(cli, ["dataset", "upload", "--path", str(tmpdir), "--repository", repository_id])
    assert result.exit_code == 0, result.stdout

    match = re.search(r"uploaded at (.+)", result.stdout)
    assert match

    id = match[1]
    id = id[:-1] # Remove tailing '.'

    result = runner.invoke(cli, ["dataset", "delete", "--repository", repository_id, "--id", id])
    assert result.exit_code == 0, result.stdout
