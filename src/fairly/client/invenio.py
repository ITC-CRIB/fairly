from typing import Dict, List, Callable

import fairly
from . import Client
from ..metadata import Metadata
from ..person import Person, PersonList
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile

import re
from urllib.parse import urlparse
import requests
from requests.exceptions import HTTPError
from collections import OrderedDict
from datetime import datetime
import logging
from functools import cached_property


CLASS_NAME = "InvenioClient"


class InvenioClient(Client):
    """
    Class Attributes:
        PAGE_SIZE (int): Default page size.
        KEEP_ALIVE (int): Keep alive seconds.

    Attributes:
        _details (Dict): Record details cache.
    """

    PAGE_SIZE = 100

    KEEP_ALIVE = 10


    def __init__(self, repository_id: str=None, **kwargs):
        super().__init__(repository_id, **kwargs)

        self._details = {}


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
        logging.info("Checking Invenio client for %s.", url)
        parts = urlparse(url)

        url = parts.scheme + "://" + parts.netloc
        api_url = url + "/api/"

        try:
            response = requests.get(api_url + "records?size=1")
            response.raise_for_status()
            data = response.json()

        except:
            raise ValueError("Invalid repository")

        if ("hits" not in data) or ("hits" not in data["hits"]):
            raise ValueError("Invalid repository")

        logging.info("Repository found at %s.", api_url)
        client = InvenioClient(name=parts.hostname, url=url, api_url=api_url)

        return client


    def _create_session(self) -> requests.Session:
        session = super()._create_session()

        # Set authentication token
        if self.config.get("token"):
            session.headers["Authorization"] = f"Bearer {self.config['token']}"

        return session


    def _get_dataset_id(self, **kwargs) -> Dict:
        """Returns standard dataset identifier.

        Args:
            **kwargs: Dataset identifier arguments.

        Returns:
            Standard dataset identifier.

        Raises:
          ValueError("Invalid URL address")
          ValueError("Invalid DOI")
          ValueError("No identifier")
        """
        if "id" in kwargs:
            id = str(kwargs["id"])

        elif "url" in kwargs:
            parts = urlparse(kwargs["url"]).path.strip("/").split("/")
            if parts and len(parts) >= 2 and re.fullmatch("(records?|uploads?)", parts[-2]):
                id = parts[-1]
            else:
                raise ValueError("Invalid URL address")

        elif "doi" in kwargs:
            try:
                logging.info("Sending DOI search query for %s.", kwargs['doi'])
                result, response = self._request(f'records?q=doi:"{kwargs["doi"]}"')
            except:
                # TODO: Add error handling
                raise ValueError("Invalid DOI")

            if "hits" not in result or not result["hits"]["hits"]:
                raise ValueError("Invalid DOI")

            id = result["hits"]["hits"][0]["id"]

        else:
            raise ValueError("No identifier")

        return {"id": id}


    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            Hash of the dataset identifier.
        """
        return id["id"]


    def _set_details(self, id: Dict, details: Dict) -> None:
        """Stores dataset details in the cache.

        Args:
            id (Dict): Standard dataset id.
            details (Dict): Dataset details. Set None to clear the cached details.
        """
        hash = self._get_dataset_hash(id)

        if details:
            logging.info("Settings dataset details for %s.", id)
            self._details[hash] = [details, datetime.now()]

        else:
            if hash in self._details:
                logging.info("Deleting dataset details for %s.", id)
                del self._details[hash]


    def _get_details(self, id: Dict) -> Dict:
        """Returns cached dataset details.

        Args:
            id (Dict): Standard dataset id.

        Returns:
            Dataset details dictionary if cache is valid, None otherwise.
        """
        hash = self._get_dataset_hash(id)

        if hash not in self._details:
            return None

        details, time = self._details[hash]

        if (datetime.now() - time).total_seconds() > self.KEEP_ALIVE:
            del self._details[hash]
            return None

        return details


    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata.

        Args:
            metadata (Metadata): Standard metadata.

        Returns:
            Standard identifier of the dataset.

        Raises:
            ValueError("No access token")
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        # Create empty dataset
        try:
            result, _ = self._request("records", "POST", data={})

        except HTTPError as err:
            # TODO: Add error handling
            raise

        # Get dataset id
        id = self.get_dataset_id(result["id"])

        # Save metadata
        try:
            self.save_metadata(id, metadata)

        except:
            self.delete_dataset(id)
            raise

        return id


    def _get_entities(self, endpoint: str, page_size: int=None, key: str=None, process: Callable=None):
        """Retrieves all entities available at the specified endpoint.

        Args:
            endpoint (str): Path of the endpoint.
            page_size (int): Page size for each retrieval step. Default page
                size is used if set to None.
            process (Callable): Callback function to process each entity.
                Retrieved entity is provided as the argument and returned value
                is stored as the entity. Retrieval is terminated if returned
                value is False.

        """
        # Set argument separator
        sep = "&" if "?" in endpoint else "?"

        # Set default page size if required
        if page_size is None or page_size < 0:
            page_size = self.PAGE_SIZE

        page = 1
        entities = {} if key else []

        while True:

            try:
                content, _ = self._request(f"{endpoint}{sep}page={page}&size={page_size}")

            except HTTPError as err:
                if page > 1 and err.response.status_code in [400, 403, 404]:
                    break
                raise

            if not content:
                break

            if isinstance(content, list):
                items = content

            elif not content["hits"] or not content["hits"]["hits"]:
                break

            else:
                items = content["hits"]["hits"]

            for item in items:

                if process:
                    entity = process(item)
                    if item is False:
                        break

                else:
                    entity = item

                if key:
                    entities[entity[key]] = entity

                else:
                    entities.append(entity)

            else:
                if len(entities) < page_size:
                    break

                page += 1
                continue

            break

        return entities


    def _get_account_datasets(self) -> List[RemoteDataset]:
        if "token" not in self.config:
            return []

        datasets = []

        items = self._get_entities("user/records")
        for item in items:

            id = {"id": item["id"]}

            self._set_details(id, item)

            dataset = RemoteDataset(self, id)
            datasets.append(dataset)

        return datasets


    def _get_dataset_details(self, id: Dict) -> Dict:
        """Retrieves dataset details.

        Args:
            id (Dict): Standard dataset id.

        Returns:
            Dictionary of dataset details.

        Raises:
            ValueError("Invalid dataset id")
        """
        details = self._get_details(id)
        if details:
            return details

        endpoints = [f"records/{id['id']}"]
        if self.config.get("token"):
            endpoints.insert(0, f"records/{id['id']}/draft")

        details = None
        for endpoint in endpoints:
            try:
                details, _ = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code in [401, 403, 404]:
                    continue
                raise

        if not details:
            raise ValueError("Invalid dataset id")

        self._set_details(id, details)

        return details


    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns standard dataset identifiers of the dataset versions.

        Args:
            id (Dict): Standard dataset id.

        Returns:
            Ordered dictionary of dataset identifiers of the available versions.
            Keys are the versions, values are the dataset identifiers.
        """
        versions = OrderedDict()

        items = self._get_entities(f"records/{id['id']}/versions?sort=-version")

        for item in items:
            version_id = {"id": item["id"]}

            versions[item["metadata"]["version"]] = version_id

            self._set_details(version_id, item)

        return versions


    def _get_metadata(self, id: Dict) -> Dict:
        """Extracts metadata from dataset details.

        Args:
            id (Dict): Standard dataset id.

        Returns:
            Dictionary of standard metadata attributes.
        """
        # Get dataset details
        details = self._get_dataset_details(id)

        # Get dataset metadata
        metadata = details["metadata"]

        # Set metadata attributes

        # REMARK: Check Invenio API documentation for more information.
        # https://inveniordm.docs.cern.ch/reference/metadata/
        attrs = {}

        for key, val in metadata.items():
            if key in ["relations"]:
                continue

            # elif key in ["creators", "contributors"]:
            #     val = PersonList([_get_person(item) for item in val])
            #
            #     if key == "creators":
            #         key = "authors"

            attrs[key] = val

        # Return metadata attributes
        return attrs


    def _serialize_metadata(self, metadata: Metadata) -> Dict:
        """Serializes dataset metadata for client use

        Args:
            metadata (Metadata): Dataset metadata

        Returns:
            Client-specific dictionary of the metadata
        """
        out = {}

        for key, val in metadata.serialize().items():
            out[key] = val

        return out


    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset

        Args:
            id (Dict): Standard dataset id
            metadata (Metadata): Metadata to be saved

        Raises:
            ValueError("No access token")
        """
        # Raise exception if no access token
        if not self.config.get("token"):
            raise ValueError("No access token")

        # Serialize metadata
        data = {"metadata": self._serialize_metadata(metadata)}

        # Save metadata
        try:
            logging.info("Saving metadata of %s.", id)
            logging.debug("Metadata %s", data)
            result, response = self._request(f"records/{id['id']}/draft", "PUT", data=data)
            logging.debug("Result %s", result)

        except HTTPError as err:
            if err.response.status_code == 400:
                raise ValueError(err.response.content)
            raise

        # Update details cache
        self._set_details(id, result)


    def validate_metadata(self, metadata: Metadata) -> Dict:
        result = {}

        # if not metadata.get("type"):
        #     result["type"] = "Type is required."
        #
        # if not metadata.get("title"):
        #     result["title"] = "Title is required."
        #
        # if not metadata.get("authors"):
        #     result["authors"] = "At least one author is required."

        return result


    def get_files(self, id: Dict) -> List[RemoteFile]:
        """Retrieves list of files of the specified dataset.

        Args:
            id (Dict): Standard dataset identifier.

        Returns:
            List of dataset files (RemoteFile).

        Raises:
            ValueError("Operation not permitted"): If files are restricted.
            ValueError("Invalid dataset id"): If invalid dataset identifier.
        """
        endpoints = [f"records/{id['id']}/files"]
        if self.config.get("token"):
            endpoints.insert(0, f"records/{id['id']}/draft/files")

        result = None
        for endpoint in endpoints:
            try:
                result, response = self._request(endpoint)
                break
            except HTTPError as err:
                if err.response.status_code == 403:
                    raise PermissionError("Operation not permitted")
                elif err.response.status_code in [401, 404]:
                    logging.info(err.response)
                    continue
                raise

        if not result:
            raise ValueError("Invalid dataset id")

        files = []
        for item in result["entries"]:
            args = {
                "id": item.get("file_id"),
                "path": item.get("key"),
                "size": item.get("size"),
                "md5": item.get("checksum"),
                "url": item["links"]["content"]
            }

            # Remove 'md5:' prefix from the checksum if required
            # REMARK: string.removeprefix() method can be used for Python 3.9+
            if args["md5"] and args["md5"].startswith("md5:"):
                args["md5"] = args["md5"][4:]

            file = RemoteFile(**args)
            files.append(file)

        return files


    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        result, response = self._request(
            f"records/{id['id']}/draft/files",
            "POST",
            data=[{"key": file.path}]
        )

        if response.status_code != 201:
            raise Exception("Invalid upload start")

        for item in result["entries"]:
            if item["key"] != file.path:
                continue
            if item["status"] != "pending":
                raise Exception(f"Invalid upload start status {item['status']}")
            break

        # TODO: Add progress monitoring support
        # TODO: Add error handling
        with open(file.fullpath, "rb") as data:
            result, response = self._request(
                f"records/{id['id']}/draft/files/{item['key']}/content",
                "PUT",
                data=data,
                serialize=False,
                headers={"Content-Type": "application/octet-stream"},
            )

        # TODO: Add error handling
        result, response = self._request(
            f"records/{id['id']}/draft/files/{item['key']}/commit",
            "POST"
        )

        remote_file = RemoteFile(
            url=result["links"]["self"],
            id=result["file_id"],
            path=result["key"],
            size=int(result["size"]),
            md5=result["checksum"][4:] if result["checksum"].startswith("md5:") else result["checksum"],
        )

        if file.size != remote_file.size or file.md5 != remote_file.md5:
            self._delete_file(id, remote_file)
            raise IOError("Invalid file upload")

        # Invalidate details cache
        self._set_details(id, None)

        return remote_file


    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        """Deletes specified file of the dataset from the repository.

        REMARK: Only draft files can be deleted.

        Args:
            id (Dict): Standard dataset identifier.
            file (RemoteFile): File

        Raises:
            ValueError("No file id"): If file has no id.
        """
        logging.log("Deleting dataset file %s : %s", id, file.id)
        if not file.id:
            raise ValueError("No file id")

        # Try to delete the file
        try:
            result, response = self._request(f"records/{id['id']}/draft/files/{file.id}", "DELETE")

        except HTTPError as err:
            # TODO: Error code 504 might be a bug (Last checked: 2023/11/20)
            if err.response.status_code == 504:
                pass
            else:
                # TODO: Add error handling
                raise

        # Invalidate details cache
        self._set_details(id, None)


    def _delete_dataset(self, id: Dict) -> None:
        """Deletes specific dataset from the repository.

        REMARK: Only draft records can be deleted.

        Args:
            id (Dict): Standard dataset identifier.

        Raises:
            ValueError("Operation not permitted")
            ValueError("Invalid dataset id")
        """
        logging.info("Deleting dataset %s.", id)
        # Try to delete the record
        try:
            result, response = self._request(f"records/{id['id']}/draft", "DELETE")

        except HTTPError as err:
            # TODO: Error code 504 might be a bug (Last checked: 2023/11/20)
            if err.response.status_code == 504:
                pass
            elif err.response.status_code == 403:
                raise ValueError("Operation not permitted")
            elif err.response.status_code == 404:
                raise ValueError("Invalid dataset id")
            else:
                raise

        # Invalidate details cache
        self._set_details(id, None)


    def get_details(self, id: Dict) -> Dict:
        """Returns standard details of the specified dataset.

        Details dictionary:
            - title (str): Title
            - url (str): URL address
            - doi (str): DOI
            - status (str): Status
            - size (int): Total size of data files in bytes (optional)
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
            id (Dict): Standard dataset id.

        Returns:
            Details dictionary of the dataset.
        """
        details = self._get_dataset_details(id)

        statuses = {
            "inprogress": "draft",
            "unsubmitted": "draft",
            "error": "error",
            "open": "public",
            "embargoed": "embargoed",
            "restricted": "restricted",
            "closed": "closed",
        }

        if "state" in details and details["state"] != "done":
            state = details["state"]

        elif "access_right" in details["metadata"]:
            state = details["metadata"]["access_right"]

        elif "access" in details:
            state = details["access"].get("status")

        else:
            state = None

        status = statuses.get(state, "unknown")

        size = None
        files = details.get("files")
        if isinstance(files, list):
            size = 0
            for file in files:
                if "size" not in file:
                    size = None
                    break
                size += file["size"]

        doi = details.get("doi")
        if not doi:
            match = re.search(Metadata.REGEXP_DOI, details["links"].get("doi", ""))
            if match:
                doi = match[0]

        modified = details.get("updated", details.get("modified"))
        if modified:
            modified = datetime.fromisoformat(modified)

        return {
            "title": details["metadata"].get("title"),
            "url": details["links"].get("self_html"),
            "doi": doi,
            "status": status,
            "size": size,
            "created": datetime.fromisoformat(details["created"]),
            "modified": modified,
        }


    @classmethod
    def supports_folder(cls) -> bool:
        return False