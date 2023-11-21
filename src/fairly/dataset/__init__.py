"""Dataset class module.

Dataset class is used to represent datasets in a standardized manner.
It is an abstract class.

Implementations:
    LocalDataset
    RemoteDataset
"""
from __future__ import annotations
from typing import List, Dict
from abc import ABC, abstractmethod

import datetime

from ..metadata import Metadata
from ..file import File
from ..diff import Diff


class Dataset(ABC):
    """Dataset class.

    Attributes:
      _metadata (Metadata): Metadata.
      _files (list): Files list.
      _modified (datetime.datetime): Last known modification date.
      _auto_refresh (bool): Auto-refresh flag.
    """

    def __init__(self, auto_refresh: bool=False):
        """Initializes Dataset object.

        Args:
            auto_refresh (bool): Set True to auto-refresh dataset information (default False).
        """
        self._metadata = None
        self._files = None
        self._modified = None
        self._auto_refresh = auto_refresh


    @abstractmethod
    def _get_metadata(self) -> Metadata:
        """Retrieves metadata of the dataset.

        Returns:
            Metadata of the dataset.
        """
        raise NotImplementedError


    def get_metadata(self, refresh: bool=False) -> Metadata:
        """Returns metadata of the dataset.

        Args:
            refresh (bool): Set True to enforce metadata retrieval (default False).

        Returns:
            Metadata of the dataset.
        """
        if self._metadata is None or refresh:
            self._metadata = self._get_metadata()
            self._modified = self.modified

        return self._metadata


    @property
    def metadata(self) -> Metadata:
        """Metadata of the dataset.

        Refreshes metadata automatically if metadata object is not modified by
        the user, auto-fresh flag is set, and metadata is modified externally.
        """
        if self._metadata and self._metadata.is_modified:
            refresh = False
        else:
            refresh = self._auto_refresh and self.is_modified

        return self.get_metadata(refresh=refresh)


    def set_metadata(self, **kwargs) -> None:
        """Sets metadata attributes.

        Args:
            **kwargs: Metadata attributes.
        """
        self.metadata.update(kwargs)


    @abstractmethod
    def _save_metadata(self) -> None:
        """Stores dataset metadata."""
        raise NotImplementedError


    def save_metadata(self, force: bool=False) -> None:
        """Stores dataset metadata if exists.

        Args:
            force (bool): Set True to enforce save even if existing dataset is modified (default False).

        Raises:
            Warning("Existing dataset is modified"): If dataset is modified.
        """
        if self._metadata is None:
            return

        # REMARK: It can be better to check if metadata is actually changed
        if self.is_modified and not force:
            raise Warning("Existing dataset is modified")

        self._save_metadata()

        self.get_metadata(refresh=True)


    @abstractmethod
    def _get_files(self) -> List[File]:
        """Returns list of files of the dataset."""
        raise NotImplementedError


    def get_files(self, refresh: bool=False) -> Dict[str, File]:
        """Returns dictionary of files of the dataset.

        Args:
            refresh (bool): Set True to enforce file list retrieval.

        Returns:
            Dictionary of files of the dataset.
            Keys are paths, values are File objects.
        """
        if self._files is None or refresh or self.auto_refresh:
            files = {}
            for file in self._get_files():
                files[file.path] = file
            self._files = files
            self._modified = self.modified

        return self._files


    @property
    def files(self) -> List[File]:
        """List of files of the dataset."""
        return self.get_files(refresh=self.is_modified)


    def get_file(self, val: str, refresh: bool=False) -> File:
        """Returns specified file of the dataset.

        Args:
            val (str): File identifier.
            refresh (bool): Set True to enforce file information retrieval.

        Returns:
            File object if file is found, None otherwise.
        """
        # TODO: Implement without using get_files()
        files = self.get_files(refresh)

        if isinstance(val, int):
            return list(files.values())[val]

        for key, file in files.items():
            if file.match(val):
                return file

        return None


    def file(self, val: str) -> File:
        """Returns specified file of the dataset.

        Automatically refreshes file information if dataset is modified.
        """
        return self.get_file(val, refresh=self.is_modified)


    @abstractmethod
    def reproduce(self) -> Dataset:
        """Reproduces an actual copy of the dataset."""
        raise NotImplementedError


    def diff_metadata(self, dataset: Dataset=None) -> Diff:
        diff = Diff()

        if dataset is None:
            dataset = self.reproduce()

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


    def diff_files(self, dataset: Dataset=None) -> Diff:
        diff = Diff()

        if dataset is None:
            dataset = self.reproduce()

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
    @abstractmethod
    def title(self) -> str:
        """Title of the dataset."""
        raise NotImplementedError


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


    @property
    def is_modified(self) -> bool:
        """Checks if the existing dataset is modified.

        Returns:
            True if the existing dataset is modified, False otherwise.
        """
        return None if self._modified is None else self._modified != self.modified


    @property
    def auto_refresh(self) -> bool:
        """Auto-refresh flag of the dataset."""
        return self._auto_refresh


    @auto_refresh.setter
    def auto_refresh(self, val) -> None:
        """Sets auto-refresh flag of the dataset."""
        self._auto_refresh = bool(val)