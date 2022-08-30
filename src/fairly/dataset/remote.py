from __future__ import annotations
from typing import List, Dict, Callable

from . import Dataset
from .local import LocalDataset
from ..metadata import Metadata
from ..file.local import LocalFile
from ..file.remote import RemoteFile
# FIXME: Importing Client results in circular dependency
# from ..client import Client

import os
import os.path

class RemoteDataset(Dataset):
    """

    Attributes:
      _client  (Client): Client object
      _id      (str)   : Dataset identifier

    """

    def __init__(self, client, id=None, **kwargs):
        """Initializes RemoteDataset object

        Arguments:
            client (Client): Client of the dataset
            id: Dataset identifier

        """
        # Call parent method
        super().__init__()
        # Set client
        self._client = client
        # Set dataset id
        self._id = client.get_dataset_id(id, **kwargs)


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


    def _set_metadata(self, metadata: Metadata) -> None:
        self.client.set_metadata(self.id, metadata)


    def _get_files(self) -> List[RemoteFile]:
        return self.client.get_files(self.id)


    def get_versions(self) -> List[RemoteDataset]:
        return self.client.get_versions(self.id)


    def serialize(self) -> Dict:
        out = super().serialize()

        out.update(self.id)
        out["client_id"] = self.client.client_id
        out["repository_id"] = self.client.repository_id

        return out


    def _download_file(self, file: RemoteFile, path: str=None, name: str=None, notify: Callable=None) -> LocalFile:
        return self.client.download_file(file, path, name, notify)


    def store(self, path: str, notify: Callable=None, extract: bool=False) -> LocalDataset:
        os.makedirs(path, exist_ok=True)
        if os.listdir(path):
            raise ValueError("Directory is not empty.")
        dataset = LocalDataset(path)
        # TODO: Set metadata directly without serialization
        dataset.set_metadata(**self.metadata.serialize())

        includes = dataset.includes
        for name, file in self.files.items():
            local_file = self._download_file(file, path, notify=notify)
            if extract and file.is_archive() and file.is_simple():
                print(f"Extract: {file.name}")
            else:
                includes.add(file.path)

        return dataset