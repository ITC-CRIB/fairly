from __future__ import annotations
from typing import List, Dict, Union
from abc import ABC, abstractmethod

from ..metadata import Metadata
from ..file import File
from ..diff import Diff


class Dataset(ABC):
    """

    Attributes:
      _metadata (Metadata): Metadata
      _files (list)       : Files list

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

        Arguments:
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


    @abstractmethod
    def _set_metadata(self, metadata: Metadata) -> None:
        raise NotImplementedError


    def set_metadata(self, **kwargs) -> None:
        # Create metadata to be updated
        metadata = Metadata(**kwargs)
        # Set metadata
        self._set_metadata(metadata)
        # Invalidate existing metadata to enforce retrieve on next request
        self._metadata = None


    @abstractmethod
    def _get_files(self) -> List[File]:
        raise NotImplementedError


    def get_files(self, refresh: bool=False) -> Dict[str, File]:
        """Returns list of files of the dataset

        Arguments:
            refresh (bool): Set True to enforce file list retrieval

        Returns:
            List of files of the dataset
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
        return self.get_files()


    def get_file(self, val: str, refresh: bool=False) -> File:
        # TODO: Implement without using get_files()
        for key, file in self.get_files(refresh).items():
            if file.match(val):
                return file

        return None


    @property
    def file(self, val: str) -> File:
        return self.get_file(val)


    def diff_metadata(self, dataset: Dataset):
        diff = Diff()
        metadata = self.metadata
        other_metadata = dataset.metadata
        for key, val in metadata.items():
            if key in other_metadata:
                pass
            else:
                pass


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


    def serialize(self) -> Dict:
        out = {}

        out["metadata"] = self.metadata.serialize()
        # out["files"] = self.serialize_files()

        return out