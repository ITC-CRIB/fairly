from typing import Any, Dict, List, Callable

from . import Client
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

    def __init__(self, repository_id: str=None, **kwargs):
        super().__init__(repository_id, **kwargs)


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters.

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


    @classmethod
    def get_client(cls, url: str) -> Client:
        """Creates a repository client from the specified URL address.

        Args:
            url (str): URL address of the repository or dataset.

        Returns:
            Client object (InvenioClient).

        Raises:
            ValueError("Invalid repository"): If repository is not valid.
        """
        logging.info("Checking Dataverse client for %s.", url)
        parts = urllib.parse.urlparse(url)

        url = parts.scheme + "://" + parts.netloc
        api_url = url + "/api/"

        try:
            response = requests.get(api_url + "search?q=&per_page=1")
            response.raise_for_status()
            data = response.json()

        except:
            raise ValueError("Invalid repository")

        if data.get("status") != "OK" or data.get("data", {}).get("q") != "":
            raise ValueError("Invalid repository")

        logging.info("Repository found at %s.", api_url)
        client = DataverseClient(url=url, api_url=api_url)

        return client


    def _create_session(self) -> requests.Session:
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
        """Returns hash of the standard dataset identifier.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Hash of the dataset identifier.
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
            HTTPError
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
        """Saves metadata of the specified dataset.

        Args:
            id (Dict): Standard dataset id.
            metadata (Metadata): Metadata to be saved.

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
        raise NotImplementedError


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
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
            id (Dict): Standard dataset id.

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        data = details["data"] if id.get("version") else details["data"]["latestVersion"]
        fields = data["metadataBlocks"]["citation"]["fields"]

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
    def supports_folder(cls) -> bool:
        """Returns if folders are supported."""
        return False
