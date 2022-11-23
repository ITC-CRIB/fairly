import pytest

@pytest.fixture(scope="session")
def dummy_dataset(tmpdir_factory):
    """Create a dummy dataset for testing"""
    # Create a dummy dataset
    dataset = tmpdir_factory.mktemp("dummy_dataset")
    for i in range(10):
        with open(f"{dataset}/file_{i}.txt", "w") as f:
            f.write(f"file_{i}")
    return dataset

# A temporary directoyr for cli testing 
@pytest.fixture(scope="session")
def cli_testing_tempdir(tmpdir_factory):
    """Create a temporary directory for testing"""
    # Create a temporary directory
    tmpdir = tmpdir_factory.mktemp("cli_testing_tempdir")
    return tmpdir