from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union
from abc import ABC, abstractmethod

import fairly
from ..dataset.remote import RemoteDataset
from ..file.local import LocalFile
from ..file.remote import RemoteFile
from ..metadata import Metadata

import os
import os.path
import re
import json
import requests
import hashlib
import http.client

REGEXP_URL = re.compile(r"^[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$", re.IGNORECASE)

class Client(ABC):
    """

    Attributes:
        config (dict) : Configuration options
        _session (Session) : HTTP session object
        _datasets (dict) : Public dataset cache
        _account_datasets (dict) : Account dataset cache
        _licenses (List) : Licenses cache

    """

    REQUEST_FORMAT = "json"

    CHUNK_SIZE = 2**16


    def __init__(self, repository_id: str=None, **kwargs):
        # Get client id
        self._client_id = self.__module__.split(".")[-1]

        # Get configuration from environmental variables by client id
        config = fairly.get_config(self._client_id)

        # Check if repository id is specified
        if repository_id:
            repository = fairly.get_repository(repository_id)
            if repository:
                if repository["client_id"] != self._client_id:
                    raise ValueError("Repository id mismatch")
                # Append configuration from repository
                config.update(repository)
                # Append configuration from environmental variables
                # REMARK: Required even if client id equal to repository id
                config.update(fairly.get_config(repository_id))
            elif re.match(REGEXP_URL, repository_id):
                kwargs["api_url"] = repository_id
        self._repository_id = repository_id

        # Append named arguments
        config.update(kwargs)

        # Set configuration
        self.config = type(self).get_config(**config)

        # Initialize attributes
        self._session = None
        self._datasets = {}
        self._account_datasets = None
        self._licenses = None



    @property
    def client_id(self) -> str:
        return self._client_id


    @property
    def repository_id(self) -> str:
        return self._repository_id


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        config = {}
        for key, val in kwargs.items():
            if key == "name":
                config["name"] = val
            elif key == "url":
                if not re.match(REGEXP_URL, val):
                    raise ValueError("Invalid URL address")
                config["url"] = val
            elif key == "api_url":
                if not re.match(REGEXP_URL, val):
                    raise ValueError(f"Invalid API URL address {val}")
                config["api_url"] = val
            else:
                pass
        return config


    def parse_id(self, id: str) -> Tuple(str, str):
        """

        Returns:
          Tuple of identifier type and value

        """
        match = re.match(r"^(doi:|https?:\/\/doi.org\/)(.+)$", id)
        if match:
            return "doi", match.group(2)
        elif re.match(r"^https?:\/\/", id):
            return "url", id
        else:
            return "id", id


    @abstractmethod
    def _get_dataset_id(self, **kwargs) -> Dict:
        raise NotImplementedError


    def get_dataset_id(self, id=None, **kwargs) -> Dict:
        if id:
            if isinstance(id, dict):
                return id
            elif isinstance(id, str):
                key, val = self.parse_id(id)
                kwargs[key] = val
            else:
                kwargs["id"] = id
        return self._get_dataset_id(**kwargs)


    @abstractmethod
    def _get_dataset_hash(self, id: Dict) -> str:
        raise NotImplementedError


    @abstractmethod
    def _create_dataset(self, metadata: Metadata) -> RemoteDataset:
        raise NotImplementedError


    def create_dataset(self, metadata=None) -> RemoteDataset:
        if metadata is None:
            metadata = Metadata()
        elif isinstance(metadata, dict):
            metadata = Metadata(**metadata)
        elif not isinstance(metadata, Metadata):
            raise ValueError("Invalid metadata")
        return self._create_dataset(metadata)


    def _create_session(self) -> Session:
        return requests.Session()


    def _request(self, endpoint: str, method: str="GET", headers: dict=None, data=None, format: str=None, serialize: bool=True) -> Tuple(Any, requests.Response):
        """ Sends a HTTP request and returns the result

        Returns:
          Returned content and response

        """

        # Patch HTTPConnection block size to improve connection speed
        # ref: https://stackoverflow.com/questions/72977722/python-requests-post-very-slow
        http.client.HTTPConnection.__init__.__defaults__ = tuple(
            x if x != 8192 else self.CHUNK_SIZE
            for x in http.client.HTTPConnection.__init__.__defaults__
        )

        # Set default data format
        if not format:
            format = self.REQUEST_FORMAT

        # Serialize data if required
        if data is not None and serialize:
            if format == "json":
                data = json.dumps(data)

        # Create session if required
        if self._session is None:
            self._session = self._create_session()

        # Build URL address
        if not self.config["api_url"]:
            raise ValueError("No API URL address")

        # TODO: Better join of endpoint
        url = self.config["api_url"] + endpoint

        _headers = headers.copy() if headers else {}
        if format == "json":
            _headers["Accept"] = "application/json"

        response = self._session.request(method, url, headers=_headers, data=data)
        response.raise_for_status()

        if response.content:
            if format == "json":
                content = response.json()
            else:
                content = response.content
        else:
            content = None

        return content, response


    @abstractmethod
    def _get_licenses(self) -> List:
        raise NotImplementedError


    def get_licenses(self, refresh: bool=False) -> List[Dict]:
        if self._licenses is None or refresh:
            self._licenses = self._get_licenses()

        return self._licenses

    @property
    def licenses(self) -> Dict:
        return self.get_licenses()


    @abstractmethod
    def _get_categories(self) -> List:
        raise NotImplementedError


    @property
    def categories(self) -> Dict:
        """Dictionary of categories recognized by the client.

        Keys are the titles of the categories.
        Values are dictionaries of category attributes.

        Attributes:
        - id: Category id if exists, otherwise None
        - parent: Parent category title if exists, otherwise None
        - parent_id: Parent category id if exists, otherwise None
        - selectable: True if category is selectable, otherwise False

        Remarks:
        Presence of parent_id does not mean that corresponding category
        is available in the dictionary. Some clients (e.g. Figshare) do not
        provide such information publicly.

        """
        if not hasattr(self, "_categories"):
            items = self._load_categories()
            self._categories = {}
            for item in items:
                category = {}
                if not item["name"]:
                    raise ValueError("No category name")
                category["id"] = item["id"] if "id" in item else None
                category["parent_id"] = item["parent_id"] if "parent_id" in item else None
                category["selectable"] = item["selectable"] if "selectable" in item else True
                category["parent"] = item["parent"] if "parent" in item else None
                if not category["parent"] and category["parent_id"]:
                    for parent in items:
                        if parent["id"] == category["parent_id"]:
                            category["parent"] = parent["name"]
                            break;
                self._categories[item["name"]] = category
        return self._categories


    @abstractmethod
    def _get_account_datasets(self) -> List[RemoteDataset]:
        raise NotImplementedError


    def get_account_datasets(self, refresh: bool=False) -> List[RemoteDataset]:
        if self._account_datasets is None or refresh:
            datasets = self._get_account_datasets()
            for dataset in datasets:
                id = dataset.id
                hash = self._get_dataset_hash(id)
                self._datasets[hash] = dataset
            self._account_datasets = datasets
        return self._account_datasets


    def get_dataset(self, id, refresh: bool=False, **kwargs) -> RemoteDataset:
        # Get standard id
        id = self.get_dataset_id(id, **kwargs)
        # Get dataset hash
        hash = self._get_dataset_hash(id)
        # Fetch dataset if required
        if hash not in self._datasets or refresh:
            self._datasets[hash] = RemoteDataset(self, id)
        # Return dataset
        return self._datasets[hash]


    @abstractmethod
    def _get_versions(self, id: Dict) -> Dict[Dict]:
        raise NotImplementedError


    def get_versions(self, id, refresh: bool=False, **kwargs) -> Dict[RemoteDataset]:
        # Get standard id
        id = self.get_dataset_id(id, **kwargs)
        datasets = {}
        versions = self._get_versions(id)
        for version, id in versions.items():
            datasets[str(version)] = self.get_dataset(id)
        return datasets


    @abstractmethod
    def get_metadata(self, id: Dict) -> Metadata:
        raise NotImplementedError


    @abstractmethod
    def set_metadata(self, id: Dict, metadata: Metadata) -> None:
        raise NotImplementedError


    @abstractmethod
    def validate_metadata(self, metadata: Metadata) -> Dict:
        """Validates metadata

        Arguments:
            metadata (Metadata): Metadata to be validated

        Returns:
            Dictionary of invalid metadata fields and related error messages,
            if any.

        """
        raise NotImplementedError


    @abstractmethod
    def get_files(self, id: Dict) -> List[RemoteFile]:
        raise NotImplementedError


    def download_file(self, file: RemoteFile, path: str=None, name: str=None, notify: Callable=None) -> LocalFile:
        if not file.url:
            raise ValueError("No URL address")
        if not path:
            path = os.getcwd()
        if not name:
            name = file.name
        fullpath = os.path.join(path, name)
        size = 0
        total_size = file.size
        md5 = hashlib.md5()
        if self._session is None:
            self._session = self._create_session()
        try:
            with self._session.get(file.url, stream=True) as response:
                response.raise_for_status()
                os.makedirs(os.path.dirname(fullpath), exist_ok=True)
                with open(fullpath, 'wb') as local_file:
                    for chunk in response.iter_content(self.CHUNK_SIZE):
                        local_file.write(chunk)
                        md5.update(chunk)
                        size += len(chunk)
                        if notify:
                            notify(file=file, size=size)
            md5 = md5.hexdigest()
            if file.md5 and file.md5 != md5:
                raise IOError("Invalid MD5 checksum")
        except:
            # Clean up if incomplete download
            # TODO: Remove created directories
            if os.path.isfile(fullpath):
                os.remove(fullpath)
            raise
        return LocalFile(fullpath, basepath=path, md5=md5)


    @abstractmethod
    def _upload_file(self, id: Dict, file: LocalFile, notify: Callable=None) -> RemoteFile:
        raise NotImplementedError


    def upload_file(self, dataset, file, notify: Callable=None) -> RemoteFile:
        if not isinstance(dataset, RemoteDataset):
            dataset = self.get_dataset(dataset)

        if not isinstance(file, LocalFile):
            file = LocalFile(file)

        remote_file = self._upload_file(dataset.id, file, notify)

        # TODO: Do not refresh the complete file list
        dataset.get_files(refresh=True)

        return remote_file


    @abstractmethod
    def _delete_file(self, id: Dict, file: RemoteFile) -> None:
        raise NotImplementedError


    def delete_file(self, dataset, file) -> None:
        if not isinstance(dataset, RemoteDataset):
            dataset = self.get_dataset(dataset)

        if not isinstance(file, RemoteFile):
            file = dataset.get_file(file)
            if not file:
                raise ValueError("Invalid file identifier")

        self._delete_file(dataset.id, file)

        # TODO: Do not refresh the complete file list
        dataset.get_files(refresh=True)
