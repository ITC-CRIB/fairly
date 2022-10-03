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

class Client(ABC):
    """

    Attributes:
        config (dict): Configuration options
        _session (Session): HTTP session object
        _datasets (dict): Public dataset cache
        _account_datasets (List): Account dataset cache
        _licenses (List): Licenses cache
    """

    REGEXP_URL = re.compile(r"^[(http(s)?):\/\/(www\.)?a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$", re.IGNORECASE)

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
            elif re.match(Client.REGEXP_URL, repository_id):
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
        """Client identifier"""
        return self._client_id


    @property
    def repository_id(self) -> str:
        """Repository identifier of the client"""
        return self._repository_id


    @classmethod
    def get_config_parameters(cls) -> Dict:
        """Returns configuration parameters

        Args:
            None

        Returns:
            Dictionary of configuration parameters.
            Keys are the parameter names, values are the descriptions.
        """
        return {
            "name": "Repository name.",
            "url": "URL address of the repository.",
            "api_url": "API end-point URL address of the repository.",
            "doi_prefixes": "DOI prefixes of the repository.",
        }


    @classmethod
    def get_config(cls, **kwargs) -> Dict:
        config = {}
        for key, val in kwargs.items():
            if key == "name":
                config["name"] = val
            elif key == "url":
                if not re.match(Client.REGEXP_URL, val):
                    raise ValueError("Invalid URL address")
                config["url"] = val
            elif key == "api_url":
                if not re.match(Client.REGEXP_URL, val):
                    raise ValueError("Invalid API URL address")
                config["api_url"] = val
            elif key == "doi_prefixes":
                if not isinstance(val, list):
                    raise ValueError("Invalid DOI prefixes")
                config["doi_prefixes"] = val
            else:
                pass
        return config


    @classmethod
    def parse_id(cls, id: str) -> Tuple(str, str):
        """Parses the specified identifier

        Returns:
          Tuple of identifier type and value
        """
        match = re.match(r"^(doi:|https?:\/\/doi.org\/)(.+)$", id)
        if match:
            return "doi", match.group(2)
        elif re.match(Metadata.REGEXP_DOI, id):
            return "doi", id
        elif re.match(r"^https?:\/\/", id):
            return "url", id
        else:
            return "id", id


    @abstractmethod
    def _get_dataset_id(self, **kwargs) -> Dict:
        raise NotImplementedError


    def get_dataset_id(self, id=None, **kwargs) -> Dict:
        """Returns standard dataset identifier

        Args:
            id: Dataset identifier
            **kwargs: Other identifier arguments

        Returns:
            Standard dataset identifier
        """
        if id:
            if isinstance(id, dict):
                return id
            elif isinstance(id, str):
                key, val = Client.parse_id(id)
                kwargs[key] = val
            else:
                kwargs["id"] = id
        return self._get_dataset_id(**kwargs)


    @abstractmethod
    def _get_dataset_hash(self, id: Dict) -> str:
        """Returns hash of the standard dataset identifier

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            Hash of the dataset identifier
        """
        raise NotImplementedError


    @classmethod
    def normalize(cls, name: str, val) -> Any:
        """Normalized metadata attribute value

        Args:
            name (str): Attribute name
            val: Attribute value

        Returns:
            Normalized attribute value
        """
        return Metadata.normalize(name, val)


    @abstractmethod
    def _create_dataset(self, metadata: Metadata) -> Dict:
        """Creates a dataset with the specified standard metadata

        Args:
            metadata (Metadata): Standard metadata

        Returns:
            Standard identifier of the dataset
        """
        raise NotImplementedError


    def create_dataset(self, metadata=None) -> RemoteDataset:
        """Creates a dataset with the specified metadata

        Args:
            metadata: Metadata of the dataset (optional)

        Returns:
            Dataset

        Raises:
            ValueError("Invalid metadata")
            ValueError("Invalid metadata", validation_result)
        """
        # Get standard metadata
        if metadata is None:
            metadata = Metadata()

        elif isinstance(metadata, dict):
            metadata = Metadata(**metadata)

        elif not isinstance(metadata, Metadata):
            raise ValueError("Invalid metadata")

        # Validate dataset
        result = self.validate_metadata(metadata)
        if result:
            raise ValueError("Invalid metadata", result)

        # Create dataset
        id = self._create_dataset(metadata)

        # Get dataset
        dataset = self.get_dataset(id)

        # Cache dataset
        hash = self._get_dataset_hash(id)
        self._datasets[hash] = dataset
        if not self._account_datasets:
            self._account_datasets = []
        self._account_datasets.append(dataset)

        # Return dataset
        return dataset


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
            if "Content-Type" not in _headers:
                _headers["Content-Type"] = "application/json"

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
    def _get_licenses(self) -> Dict:
        raise NotImplementedError


    def get_licenses(self, refresh: bool=False) -> List[Dict]:
        """Returns list of available licenses

        Args:
            refresh (bool): Set True to refresh licenses (default = False)

        Returns:
            List of client-specific license dictionaries
        """
        if self._licenses is None or refresh:
            self._licenses = self._get_licenses()

        return self._licenses


    @property
    def licenses(self) -> Dict:
        return self.get_licenses()


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
    def _get_versions(self, id: Dict) -> OrderedDict:
        """Returns dataset ids of the available dataset versions

        Some clients do not provide information to order versions (e.g. date).
        Therefore, ordered dictionary is needed to have properly ordered
        versions as reported by the client.

        Args:
            id (Dict): Dataset id

        Returns:
            Ordered dictionary of dataset ids of the available versions.
            Keys are the versions, values are the dataset ids.
        """
        raise NotImplementedError


    def get_versions(self, id, refresh: bool=False, **kwargs) -> List[RemoteDataset]:
        """Returns datasets of all available versions of the specified dataset

        Args:
            id: Dataset identifier
            refresh (bool): Set True to refresh versions (default = False)

        Returns:
            List of datasets of all available versions
        """
        # Get standard id
        id = self.get_dataset_id(id, **kwargs)

        # Get versions
        versions = self._get_versions(id)

        # Get datasets
        datasets = []
        for id in versions:
            datasets.append(self.get_dataset(id))

        # Return datasets
        return datasets


    @abstractmethod
    def _get_metadata(self, id: Dict) -> Dict:
        """Returns standard metadata attributes

        Args:
            id (Dict): Standard dataset id

        Returns:
            Dictionary of standard metadata attributes
        """
        raise NotImplementedError


    def get_metadata(self, id: Dict) -> Metadata:
        """Returns standard metadata of the specified dataset

        Args:
            id (Dict): Standard dataset id

        Returns:
            Standard metadata
        """
        # Get standard metadata attributes
        attrs = self._get_metadata(id)

        # Append repository attributes
        if self.repository_id:
            attrs[f"{self.repository_id}_id"] = id

        # Return metadata
        return Metadata(normalize=self.normalize, **attrs)


    @abstractmethod
    def save_metadata(self, id: Dict, metadata: Metadata) -> None:
        """Saves metadata of the specified dataset

        Args:
            id (Dict): Standard dataset id
            metadata (Metadata): Metadata to be saved

        Returns:
            None
        """
        raise NotImplementedError


    @abstractmethod
    def validate_metadata(self, metadata: Metadata) -> Dict:
        """Validates metadata

        Args:
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


    @abstractmethod
    def _delete_dataset(self, id: Dict) -> None:
        """Deletes dataset specified by the standard identifier from the repository

        Args:
            id (Dict): Standard dataset identifier

        Returns:
            None

        Raises:
            ValueError("Operation not permitted")
            ValueError("Invalid dataset id")
        """
        raise NotImplementedError


    def delete_dataset(self, id, **kwargs) -> None:
        """Deletes specified dataset from the repository

        Args:
            id: Dataset identifier
            **kwargs: Other identifier arguments

        Returns:
            None
        """
        # Get standard id
        id = self.get_dataset_id(id, **kwargs)

        # Delete dataset
        self._delete_dataset(id)

        # Delete from the dataset cache if exists
        hash = self._get_dataset_hash(id)
        if hash in self._datasets:
            del self._datasets[hash]

        # Delete from the account dataset cache if exists
        if self._account_datasets:
            for i, dataset in enumerate(self._account_datasets):
                if id == dataset.id:
                    del self._account_datasets[i]
                    break


    @abstractmethod
    def get_status(self, id: Dict) -> str:
        """Returns status of the specified dataset

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "error": Dataset is in an error state.

        Args:
            id (Dict): Standard dataset id

        Returns:
            Status of the dataset.

        Raises:
            ValueError("Invalid dataset id")
        """
        raise NotImplementedError


    @abstractmethod
    def get_dates(self, id: Dict) -> Dict:
        """Returns date dictionary of the specified dataset

        Date dictionary:
            - created (datetime.datetime): Creation date and time
            - modified (datetime.datetime): Last modification date and time

        Args:
            id (Dict): Standard dataset id

        Returns:
            Date dictionary of the dataset.
        """
        raise NotImplementedError