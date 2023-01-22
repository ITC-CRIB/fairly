import dotenv

import pytest

@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # Load environment variables
    dotenv.load_dotenv()


@pytest.fixture(scope="session")
def dummy_dataset(tmpdir_factory):
    """Create a dummy dataset for testing.

    Returns:
        Dummy dataset path
    """
    path = tmpdir_factory.mktemp("dummy_dataset")

    for i in range(10):
        with open(path / f"file_{i}.txt", "w") as file:
            file.write(f"file_{i}")

    return path
