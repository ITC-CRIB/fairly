from typing import Dict, List, Callable

from . import Client
from ..metadata import Metadata
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

from requests import Session
from collections import OrderedDict
import urllib.parse

CLASS_NAME = "DataverseClient"

class DataverseClient(Client):

    def __init__(self, repository_id: str=None, **kwargs):
        super().__init__(repository_id, **kwargs)


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters

        Args:
            None

        Returns:
            Dictionary of configuration parameters.
            Keys are the parameter names, values are the descriptions.
        """
        return {**super().get_config_parameters(), **{
            "token": "Access token.",
        }}


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        config = super().get_config(**kwargs)

        for key, val in kwargs.items():
            if key == "token":
                config["token"] = val
            else:
                pass

        return config


    def _create_session(self) -> Session:
        session = super()._create_session()

        # Set authentication token
        if self.config.get("token"):
            session.headers["X-Dataverse-key"] = self.config['token']

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """Returns standard dataset identifier.

        Args:
            **kwargs: Dataset identifier arguments

        Returns:
            Standard dataset identifier

        Raises:
          ValueError("Invalid id")
          ValueError("Invalid URL address")
          ValueError("No identifier")

        """
        if "doi" in kwargs:
            doi = kwargs["doi"]

        elif "url" in kwargs:
            url = urllib.parse.urlparse(kwargs["url"])
            params = urllib.parse.parse_qs(url.query)
            if "persistentId" in params:
                id = params["persistentId"][0]
                if id.startswith("doi:"):
                    doi = id[4:]
                else:
                    raise ValueError("Invalid id")
            else:
                raise ValueError("Invalid URL address")

        else:
            raise ValueError("No identifier")

        return {"doi": doi}


    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            Hash string of the dataset identifier
        """
        return id["doi"]


    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata

        Args:
            metadata (Metadata): Standard metadata

        Returns:
            Standard identifier of the dataset

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _get_account_datasets(self) -> List[RemoteDataset]:
        if "token" not in self.config:
            return []

        raise NotImplementedError


    def _get_licenses(self) -> Dict:
        """Retrieves the list of available licenses

        Returns:
            Dictionary of available licenses

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions

        Args:
            id (Dict): Dataset id

        Returns:
            Ordered dictionary of dataset identifiers of the available versions.
            Keys are the versions, values are the dataset identifiers.
        """
        raise NotImplementedError


    def _get_metadata(self, id: Dict) -> Dict:
        endpoint = f"datasets/:persistentId/?persistentId=doi:{id['doi']}"

        details, _ = self._request(endpoint)

        return details


    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset

        Args:
            id (Dict): Standard dataset id
            metadata (Metadata): Metadata to be saved

        Returns:
            None

        Raises:
            ValueError("No access token")
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        raise NotImplementedError


    def validate_metadata(self, metadata: Metadata) -> Dict:
        raise NotImplementedError


    def get_files(self, id: Dict) -> List[RemoteFile]:
        raise NotImplementedError


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        raise NotImplementedError


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        raise NotImplementedError


    def _delete_dataset(self, id: Dict) -> None:
        """Deletes dataset specified by the standard identifier from the repository

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            None

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def get_details(self, id: Dict) -> Dict:
        """Returns standard details of the specified dataset.

        Details dictionary:
            - title (str): Title
            - url (str): URL address
            - doi (str): DOI
            - status (str): Status
            - size (int): Total size of data files in bytes
            - created (datetime.datetime): Creation date and time
            - modified (datetime.datetime): Last modification date and time

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "error": Dataset is in an error state.
            - "unknown": Dataset is in an unknown state.

        Args:
            id (Dict): Standard dataset id

        Returns:
            Details dictionary of the dataset.
        """
        raise NotImplementedError


    @classmethod
    def supports_folder(cls) -> bool:
        return False