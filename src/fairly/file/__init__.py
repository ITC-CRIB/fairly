from abc import ABC, abstractmethod

import os.path

class File(ABC):

    @abstractmethod
    def __init__(self):
        raise NotImplementedError


    def __repr__(self):
        return repr(self.path)


    @property
    def name(self) -> str:
        """
        Name of the file including its extension.
        """
        return self._name


    @property
    def path(self) -> str:
        """
        Path of the file including its name.
        """
        return self._path


    @property
    def size(self) -> int:
        """
        Size of the file in bytes.
        """
        return self._size


    @property
    def type(self) -> str:
        """
        MIME type of the file.
        """
        return self._type


    @property
    def md5(self) -> str:
        """
        MD5 hash of the file.
        """
        return self._md5


    @property
    def extension(self) -> str:
        """
        Extension of the file.
        """
        if not hasattr(self, "_extension"):
            _, self._extension = os.path.splitext(self.name)
        return self._extension


    def match(self, val: str) -> bool:
        return True if self.name == val or self.path == val or self.md5 == val else False


    def is_simple(self) -> bool:
        """
        Returns True if the file path does not include directories, i.e. the
        path is equal to the name.
        """
        return self.path == self.name
