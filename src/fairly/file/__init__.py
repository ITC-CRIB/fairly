"""File class module.

File class is used to store file information in a standardized manner.
It is an abstract class.

Implementations:
    - LocalFile
    - RemoteFile
"""
from abc import ABC, abstractmethod

import os.path


class File(ABC):
    """File class.

    Attributes:
        _name (str): Name of the file including its extension.
        _path (str): Path of the file including its name.
        _size (int): Size of the file in bytes.
        _type (str): Content type of the file.
        _md5 (str): MD5 checksum of the file.
        _extension (str): Extension of the file.
    """

    @abstractmethod
    def __init__(self):
        """Initializes File object."""
        raise NotImplementedError


    def __repr__(self):
        """Returns string representation of the file."""
        return f"{{'path': {self.path}, 'size': {self.size}}}"


    @property
    def name(self) -> str:
        """Name of the file including its extension."""
        return self._name


    @property
    def path(self) -> str:
        """Path of the file including its name."""
        return self._path


    @property
    def size(self) -> int:
        """Size of the file in bytes."""
        return self._size


    @property
    def type(self) -> str:
        """Content type of the file."""
        return self._type


    @property
    def md5(self) -> str:
        """MD5 checksum of the file."""
        return self._md5


    @property
    def extension(self) -> str:
        """Extension of the file."""
        if not hasattr(self, "_extension"):
            _, self._extension = os.path.splitext(self.name)

        return self._extension


    def match(self, val: str) -> bool:
        """Checks if file matches the specified file identifier.

        File name, path, and MD5 checksum are compared with the specified
        identifier for matching.

        Args:
            val (str): File identifier.

        Returns:
            True if file matches the specified file identifier, False otherwise.
        """
        return True if self.name == val or self.path == val or self.md5 == val else False


    @property
    def is_simple(self) -> bool:
        """Checks if file is a simple file.

        A simple file does not include any directories in its path, e.g. the
        path is equal to the name.

        Returns:
            True if the file is simple, False otherwise.
        """
        return self.path == self.name
