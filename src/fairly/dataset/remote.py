from __future__ import annotations
from typing import List, Dict, Callable

import fairly

from . import Dataset
from ..metadata import Metadata
from ..file.local import LocalFile
from ..file.remote import RemoteFile
# FIXME: Importing Client results in circular dependency
# from ..client import Client

import os
import datetime
from functools import cached_property

class RemoteDataset(Dataset):
    """

    Attributes:
        _client (Client): Client object
        _id (str): Dataset identifier
        _details (Dict): Dataset details

    """

    def __init__(self, client, id=None, auto_refresh: bool=True, details: Dict=None, **kwargs):
        """Initializes RemoteDataset object.

        Args:
            client (Client): Client of the dataset
            id: Dataset identifier
            auto_refresh (bool): Set True to auto-refresh dataset information
        """
        # Call parent method
        super().__init__(auto_refresh=auto_refresh)
        # Set client
        self._client = client
        # Set dataset id
        self._id = client.get_dataset_id(id, **kwargs)

        if id and isinstance(id, str):
            key, val = Client.parse_id(id)
            kwargs[key] = val

        # REMARK: User-specific details should be validated once actual details becomes available
        self._details = None if not details else details.copy()


    @property
    def client(self) -> Client:
        """Client of the dataset"""
        return self._client


    @property
    def id(self) -> Dict:
        """Identifier of the dataset"""
        return self._id


    def _get_metadata(self) -> Metadata:
        return self.client.get_metadata(self.id)


    def _save_metadata(self) -> None:
        return self.client.save_metadata(self.id, self.metadata)


    def _get_files(self) -> List[RemoteFile]:
        return self.client.get_files(self.id)


    def get_versions(self) -> List[RemoteDataset]:
        return self.client.get_versions(self.id)


    def _download_file(self, file: RemoteFile, path: str=None, name: str=None, notify: Callable=None) -> LocalFile:
        return self.client.download_file(file, path, name, notify)


    def store(self, path: str=None, notify: Callable=None, extract: bool=False) -> LocalDataset:
        if not path:
            path = self.doi
            if not path:
                raise ValueError("Empty path.")
            for sep in ["/", "\\"]:
                path = path.replace(sep, "_")

        os.makedirs(path, exist_ok=True)
        if os.listdir(path):
            raise ValueError("Directory is not empty.")

        templates = fairly.metadata_templates()
        if self.client.repository_id in templates:
            template = self.client.repository_id
        elif self.client.client_id in templates:
            template = self.client.client_id
        else:
            template = None

        dataset = fairly.init_dataset(path, template=template)

        # TODO: Set metadata directly without serialization
        dataset.set_metadata(**self.metadata)
        dataset.save_metadata()

        includes = dataset.includes
        for name, file in self.files.items():
            local_file = self._download_file(file, path, notify=notify)
            if extract and local_file.is_archive and local_file.is_simple:
                files = local_file.extract(path, notify=notify)
                includes.append({file.path: files})
                os.remove(local_file.fullpath)
            else:
                includes.append(file.path)
        dataset.save_files()

        if self.client.repository_id:
            dataset.set_remote_dataset(self)

        return dataset


    def _get_detail(self, key: str, refresh: bool=False) -> Any:
        if not self._details or key not in self._details or refresh:
            self._details = self.client.get_details(self.id)

        return self._details.get(key)


    @property
    def title(self) -> str:
        """Title of the dataset."""
        # REMARK: Title is usually part of the metadata
        return self._get_detail("title")


    @property
    def url(self) -> str:
        """URL address of the dataset."""
        # REMARK: URL address might be part of the metadata
        return self._get_detail("url")


    @property
    def doi(self) -> str:
        """DOI of the dataset."""
        # REMARK: DOI might be part of the metadata
        return self._get_detail("doi")


    @property
    def status(self) -> str:
        """Status of the dataset.

        Possible statuses are as follows:
            - "draft": Dataset is not published yet.
            - "public": Dataset is published and is publicly available.
            - "embargoed": Dataset is published, but is under embargo.
            - "restricted": Dataset is published, but accessible only under certain conditions.
            - "closed": Dataset is published, but accessible only by the owners.
            - "error": Dataset is in an error state.
            - "unknown": Dataset is in an unknown state.
        """
        return self._get_detail("status")


    @property
    def size(self) -> int:
        """Total size of the dataset in bytes."""
        return self._get_detail("size")


    @cached_property
    def created(self) -> datetime.datetime:
        """Creation date and time of the dataset"""
        return self._get_detail("created")


    @property
    def modified(self) -> datetime.datetime:
        """Last modification date and time of the dataset"""
        # REMARK: Can be better to have a dedicated method to minimize data transfer
        return self._get_detail("modified", refresh=True)


    def reproduce(self) -> RemoteDataset:
        """Reproduces an actual copy of the dataset."""
        return RemoteDataset(self.client, self.id)