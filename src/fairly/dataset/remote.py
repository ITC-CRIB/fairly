from __future__ import annotations
from typing import Any, List, Dict, Callable

import fairly

from . import Dataset
from ..metadata import Metadata
from ..file.local import LocalFile
from ..file.remote import RemoteFile
# FIXME: Importing Client or LocalDataset results in circular dependency
# from ..client import Client

import os
import os.path
import datetime
import concurrent.futures
from functools import cached_property
import logging


class RemoteDataset(Dataset):
    """

    Attributes:
        _client (Client): Client object
        _id (str): Dataset identifier
        _details (Dict): Dataset details

    """

    def __init__(self, client, id=None, auto_refresh: bool=True, **kwargs):
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

        # Set details
        self._details = client.get_details(self.id)


    @property
    def client(self) -> Client:
        """Client of the dataset."""
        return self._client


    @property
    def id(self) -> Dict:
        """Identifier of the dataset."""
        return self._id


    @property
    def plain_id(self) -> str:
        """Plain identifier of the dataset."""
        return self._client.get_dataset_plain_id(self._id)


    def _get_metadata(self) -> Metadata:
        return self.client.get_metadata(self.id)


    def _save_metadata(self) -> None:
        return self.client.save_metadata(self.id, self.metadata)


    def _get_files(self) -> List[RemoteFile]:
        return self.client.get_files(self.id)


    def get_versions(self) -> List[RemoteDataset]:
        """Returns all available versions of the dataset.

        Returns:
            List of remote datasets of all available versions.
        """
        return self.client.get_versions(self.id)


    def _store_file(self, file, path, extract, notify):
        # Download file
        local_file = self.client.download_file(file, path, notify=notify)

        # Check if file should be extracted
        if extract and local_file.is_archive and local_file.is_simple:

            # Start extraction loop
            while True:
                files = local_file.extract(path, notify=notify)
                os.remove(local_file.fullpath)

                if len(files) == 1:
                    inner_file = LocalFile(os.path.join(path, files[0]))
                    if inner_file.is_archive:
                        local_file = inner_file
                        continue

                break

            return {file.path: files}

        else:
            return file.path


    def store(self, path: str=None, notify: Callable=None, extract: bool=False, max_workers: int=None) -> LocalDataset:
        """Stores the dataset to a local directory.

        If no path is provided, DOI is used by replacing slashes and backslashes with underscores.
        Local directory is created if it does not exist.

        Args:
            path (str): Path to the local directory (optional).
            notify (Callable): Notification callback method (optional).
            extract (bool): Set True to extract archive files (default False).
            max_workers (int): Number of workers (optional).

        Returns:
            LocalDataset object of the stored local dataset.

        Raises:
            ValueError("Empty path")
            ValueError("Directory is not empty")
        """
        # Set number of workers if required
        if not max_workers:
            max_workers = fairly.max_workers()

        # Set path based on DOI if required
        if not path:
            path = self.doi
            if not path:
                raise ValueError("Empty path")
            for sep in ["/", "\\"]:
                path = path.replace(sep, "_")

        # Create path
        os.makedirs(path, exist_ok=True)

        # check if directory is empty,
        # while ignoring hidden files or directories
        entries = os.listdir(path)
        visible_entries = [entry for entry in entries if not entry.startswith(".")]
        if len(visible_entries) > 0:
            raise ValueError("Directory is not empty.")

        # Set dataset template
        templates = fairly.metadata_templates()

        if self.client.repository_id in templates:
            template = self.client.repository_id

        elif self.client.client_id in templates:
            template = self.client.client_id

        else:
            template = None

        # Initialize dataset
        dataset = fairly.init_dataset(path, template=template)

        # Save metadata
        # TODO: Set metadata directly without serialization
        dataset.set_metadata(**self.metadata)
        dataset.save_metadata()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

            futures = []

            for _, file in self.files.items():
                futures.append(
                    executor.submit(self._store_file, file, path, extract, notify)
                )

            for future in concurrent.futures.as_completed(futures):
                dataset.includes.append(future.result())

        # Save file information
        dataset.save_files()

        # Set remote dataset id if possible
        # REMARK: It might be possible to store configuration for custom clients.
        if self.client.repository_id:
            dataset.set_remote_dataset(self)

        return dataset


    def _get_detail(self, key: str, refresh: bool=False) -> Any:
        if refresh:
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
        size = self._get_detail("size")

        if size is None:
            size = 0
            for file in self.get_files():
                size += file.size

        return size


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