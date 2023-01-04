from __future__ import annotations
from typing import List, Dict, Union
from abc import ABC, abstractmethod
from functools import cached_property

import datetime

from ..metadata import Metadata
from ..file import File
from ..diff import Diff


class Dataset(ABC):
    """

    Attributes:
      _metadata (Metadata): Metadata
      _files (list): Files list

    """

    def __init__(self):
        self._metadata = None
        self._files = None


    @abstractmethod
    def _get_metadata(self) -> Metadata:
        """Retrieves metadata of the dataset

        Returns:
            Metadata of the dataset
        """
        raise NotImplementedError


    def get_metadata(self, refresh: bool=False) -> Metadata:
        """Returns metadata of the dataset

        Args:
            refresh (bool): Set True to enforce metadata retrieval

        Returns:
            Metadata of the dataset
        """
        if self._metadata is None or refresh:
            self._metadata = self._get_metadata()
        return self._metadata


    @property
    def metadata(self) -> Metadata:
        """Metadata of the dataset"""
        return self.get_metadata()


    def set_metadata(self, **kwargs) -> None:
        self.get_metadata().update(kwargs)


    @abstractmethod
    def save_metadata(self) -> None:
        """Stores dataset metadata"""
        raise NotImplementedError


    @abstractmethod
    def _get_files(self) -> List[File]:
        raise NotImplementedError


    def get_files(self, refresh: bool=False) -> Dict[str, File]:
        """Returns dictionary of files of the dataset

        Args:
            refresh (bool): Set True to enforce file list retrieval

        Returns:
            Dictionary of files of the dataset (key = path, value = File object)
        """
        if self._files is None or refresh:
            files = {}
            for file in self._get_files():
                files[file.path] = file
            self._files = files
        return self._files


    @property
    def files(self) -> List[File]:
        """List of files of the dataset"""
        return self.get_files(refresh=True)


    def get_file(self, val: str, refresh: bool=False) -> File:
        # TODO: Implement without using get_files()
        for key, file in self.get_files(refresh).items():
            if file.match(val):
                return file

        return None


    @property
    def file(self, val: str) -> File:
        return self.get_file(val)


    def add_file(self, file) -> File:
        raise NotImplementedError


    def remove_file(self, file) -> None:
        raise NotImplementedError


    def save_files(self) -> None:
        raise NotImplementedError


    def save(self) -> None:
        self.save_metadata()
        self.save_files()


    def diff_metadata(self, dataset: Dataset):
        diff = Diff()

        metadata = self.metadata
        other_metadata = dataset.metadata

        for key, val in metadata.items():

            if key in other_metadata:
                if val == other_metadata[key]:
                    pass
                else:
                    diff.modify(key, val, other_metadata[key])

            else:
                diff.add(key, val)

        for key, val in other_metadata.items():
            if key not in metadata:
                diff.remove(key, val)

        return diff


    def diff_files(self, dataset: Dataset) -> Diff:
        diff = Diff()

        files = self.files
        other_files = dataset.files

        for path, file in files.items():
            other_file = other_files.get(path)

            if other_file:
                if file.size == other_file.size and file.md5 == other_file.md5:
                    pass
                else:
                    diff.modify(path, file, other_file)

            else:
                diff.add(path, file)

        for path, other_file in other_files.items():
            if path not in files:
                diff.remove(path, other_file)

        return diff


    @property
    def title(self) -> str:
        """Title of the dataset."""
        return self.metadata["title"]


    @property
    @abstractmethod
    def size(self) -> int:
        """Total size of the dataset in bytes."""
        raise NotImplementedError


    @property
    @abstractmethod
    def created(self) -> datetime.datetime:
        """Creation date and time of the dataset."""
        raise NotImplementedError


    @property
    @abstractmethod
    def modified(self) -> datetime.datetime:
        """Last modification date and time of the dataset."""
        raise NotImplementedError