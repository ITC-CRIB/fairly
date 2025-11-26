"""DataverseClient class module."""
from typing import Any, Dict, List, Callable

from . import Client, ClientInfo
from ..metadata import Metadata
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

import requests
from collections import OrderedDict
import urllib.parse
import dateutil.parser
import logging


CLASS_NAME = "DataverseClient"


class DataverseClient(Client):
    """Dataverse client class."""

    def __init__(self, repository_id: str=None, **kwargs):
        """Initializes Dataverse client object.

        Args:
            repository_id (str): Repository id (optional).
            **kwargs (Dict): Client-specific configuration arguments.
        """
        super().__init__(repository_id, **kwargs)


    @classmethod
    def get_client_info(cls) -> ClientInfo:
        """Returns client information."""
        return ClientInfo(
            name="Dataverse",
            description="""
                The Dataverse is an open source web application to share,
                preserve, cite, explore and analyze research data.
            """,
            url="https://dataverse.org/",
        )


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters.

        Returns:
            Dictionary of configuration parameters {name: description}.
        """
        return {**super().get_config_parameters(), **{
            "token": "Access token.",
        }}


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        """Returns client configuration.

        Args:
            **kwargs (Dict): Client-specific configuration arguments.

        Returns:
            Dictionary of configuration arguments {name: value}.
        """
        config = super().get_config(**kwargs)

        for key, val in kwargs.items():
            if key == "token":
                config["token"] = val
            else:
                pass

        return config


    @classmethod
    def get_client(cls, url: str) -> "DataverseClient":
        """Creates a repository client from the specified URL address.

        Args:
            url (str): URL address of the repository or dataset.

        Returns:
            Client object (DataverseClient).

        Raises:
            ValueError("Invalid repository"): If repository is not valid.
        """
        logging.info("Checking Dataverse client for %s.", url)
        parts = urllib.parse.urlparse(url)

        url = parts.scheme + "://" + parts.netloc
        api_url = url + "/api/"

        try:
            # REMARK: search endpoint is not used as it may require access token
            response = requests.get(api_url + "info/metrics/dataverses")
            response.raise_for_status()
            data = response.json()

        except:
            raise ValueError("Invalid repository")

        if data.get("status") != "OK" or data.get("data", {}).get("count") is None:
            raise ValueError("Invalid repository")

        logging.info("Repository found at %s.", api_url)
        client = DataverseClient(name=parts.hostname, url=url, api_url=api_url)

        return client


    def _create_session(self) -> requests.Session:
        """Creates a session.

        Returns:
            Session (requests.Session).
        """
        session = super()._create_session()

        # Set authentication token
        if self.config.get("token"):
            session.headers["X-Dataverse-key"] = self.config['token']

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """Returns standard dataset identifier.

        Args:
            **kwargs (Dict): Dataset identifier arguments.

        Returns:
            Standard dataset identifier (Dict).

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
        """Returns hash of the standard dataset identifier.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Hash of the dataset identifier (str).
        """
        return id["doi"]


    def _get_dataset_details(self, id: Dict) -> Dict:
        """Retrieves details of the dataset.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Dictionary of dataset details.

        Raises:
            ValueError("Invalid dataset id")
        """
        if id.get("version"):
            endpoint = f"datasets/:persistentId/versions/{id['version']}?persistentId=doi:{id['doi']}"
        else:
            endpoint = f"datasets/:persistentId/?persistentId=doi:{id['doi']}"

        result, response = self._request(endpoint)

        if not result or result.get("status") != "OK" or not result.get("data"):
            raise ValueError("Invalid dataset id")

        return result


    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata.

        Args:
            metadata (Metadata): Standard metadata.

        Returns:
            Standard dataset identifier (Dict).

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _get_account_datasets(self) -> List[RemoteDataset]:
        """Retrieves list of account datasets.

        Returns:
            List of datasets related to the account ([RemoteDataset]).

        Raises:
            NotImplementedError
        """
        if "token" not in self.config:
            return []

        raise NotImplementedError


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Ordered dictionary of dataset identifiers of the available versions {version: id}.
        """
        raise NotImplementedError


    def _get_metadata(self, id: Dict) -> Dict:
        """Returns standard metadata attributes.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Dictionary of standard metadata attributes {name: value}.
        """
        details = self._get_dataset_details(id)

        data = details["data"] if id.get("version") else details["data"]["latestVersion"]
        if "citation" in data["metadataBlocks"]:
            citation = data["metadataBlocks"]["citation"]
        else:
            citation = next(iter(data["metadataBlocks"].values()))
        fields = citation["fields"]

        metadata = {}
        for field in fields:
            key = field["typeName"]
            val = self._get_property_value(field)
            metadata[key] = val

        return metadata


    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset.

        Args:
            id (Dict): Standard dataset identifier.
            metadata (Metadata): Metadata to be saved.

        Raises:
            ValueError("No access token")
            NotImplementedError
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        raise NotImplementedError


    def validate_metadata(self, metadata: Metadata) -> Dict:
        """Validates metadata.

        Args:
            metadata (Metadata): Metadata to be validated.

        Returns:
            Dictionary of invalid metadata {name: error message}.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def get_files(self, id: Dict) -> List[RemoteFile]:
        """Retrieves list of files of the specified dataset.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            List of dataset files ([RemoteFile]).
        """
        # REMARK: Dataverse has a dedicated endpoint for files
        details = self._get_dataset_details(id)

        data = details["data"] if id.get("version") else details["data"]["latestVersion"]

        if "files" not in data:
            raise NotImplementedError

        files = [];
        for item in data["files"]:
            file = item["dataFile"]
            md5 = file.get("md5")
            if not md5 and "checksum" in file and file["checksum"]["type"] == "md5":
                md5 = file["checksum"]["value"]
            file = RemoteFile(
                url=self.config.get("api_url") + f"access/datafile/{file['id']}",
                id=file.get("id"),
                path=file.get("filename"),
                size=file.get("filesize"),
                type=file.get("contentType"),
                md5=md5
            )
            files.append(file)

        return files


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        """Uploads a local file to the specified dataset at the repository.

        Args:
            id (Dict): Standard dataset identifier.
            file (LocalFile): File to be uploaded.
            notify (Callable): Notification callback method.

        Returns:
            Remote file object of the uploaded file (RemoteFile).

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        """Deletes specified file of the dataset.

        Args:
            id (Dict): Standard dataset identifier.
            file (RemoteFile): File to be deleted.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _delete_dataset(self, id: Dict) -> None:
        """Deletes specific dataset from the repository.

        Args:
            id (Dict): Standard dataset identifier.

        Raises:
            NotImplementedError
        """
        raise NotImplementedError


    def _get_property_value(self, prop: Dict) -> Any:
        """Returns metadata property value.

        Args:
            prop (Dict): Metadata property.

        Returns:
            Metadata property value.

        Raises:
            ValueError("Invalid property type class")
        """
        if prop["typeClass"] in ["primitive", "controlledVocabulary"]:
            return prop["value"]

        elif prop["typeClass"] == "compound":
            if prop["multiple"]:
                results = []
                for item in prop["value"]:
                    result = {}
                    for key, val in item.items():
                        result[key] = self._get_property_value(val)
                    results.append(result)
                return results

            else:
                result = {}
                for key, val in prop["value"].items():
                    result[key] = self._get_property_value(val)
                return result

        else:
            raise ValueError("Invalid property type class", prop["typeClass"])


    def _get_field_value(self, fields: Dict, key: str) -> Any:
        """Returns value of a specified field.

        Args:
            fields (Dict): Fields.
            key (str): Field key.

        Returns:
            Field value if exists, None otherwise.
        """
        for field in fields:
            if field["typeName"] == key:
                return self._get_property_value(field)
                break

        return None


    def get_details(self, id: Dict) -> Dict:
        """Returns standard details of the specified dataset.

        Details dictionary:
            - title (str): Title.
            - url (str): URL address.
            - doi (str): DOI.
            - status (str): Status.
            - size (int): Total size of data files in bytes.
            - created (datetime.datetime): Creation date and time.
            - modified (datetime.datetime): Last modification date and time.

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "error": Dataset is in an error state.
            - "unknown": Dataset is in an unknown state.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        data = details["data"] if id.get("version") else details["data"]["latestVersion"]
        if "citation" in data["metadataBlocks"]:
            citation = data["metadataBlocks"]["citation"]
        else:
            citation = next(iter(data["metadataBlocks"].values()))
        fields = citation["fields"]

        out = {}

        out["title"] = self._get_field_value(fields, "title")
        if isinstance(out["title"], list):
            out["title"] = out["title"][0]

        url = self.config.get("url")
        if url:
            out["url"] = f"{url}/dataset.xhtml?persistentId=doi:{id['doi']}"
            if id.get("version"):
                out["url"] += f"&version={id['version']}"

        out["doi"] = data["datasetPersistentId"]
        if out["doi"].startswith("doi:"):
            out["doi"] = out["doi"][4:]

        # TODO: Set status

        # REMARK: Dataverse has a dedicated endpoint for dataset size
        # https://guides.dataverse.org/en/latest/api/native-api.html?highlight=typename#id81
        if "files" in data:
            size = 0
            for file in data["files"]:
                size += file["dataFile"]["filesize"]
            out["size"] = size

        out["created"] = dateutil.parser.isoparse(data["createTime"])
        out["modified"] = dateutil.parser.isoparse(data["lastUpdateTime"])

        return out


    @classmethod
    def supports_folders(cls) -> bool:
        """Returns if folders are supported.

        Returns:
            True if folders are supported, False otherwise.
        """
        return False
