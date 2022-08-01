from abc import ABC, abstractmethod

import os.path

class File(ABC):

    archive_types = (
        "application/gzip",
        "application/x-bzip",
        "application/x-bzip2",
        "application/x-tar",
        "application/zip",
        "application/x-zip-compressed",
    )

    @abstractmethod
    def __init__(self):
        raise NotImplementedError


    def __repr__(self):
        return repr(self.path)


    @property
    def name(self) -> str:
        return self._name


    @property
    def path(self) -> str:
        return self._path


    @property
    def size(self) -> int:
        return self._size


    @property
    def type(self) -> str:
        return self._type


    @property
    def md5(self) -> str:
        return self._md5


    @property
    def extension(self) -> str:
        if not hasattr(self, "_extension"):
            _, self._extension = os.path.splitext(self.name)
        return self._extension
        

    def match(self, val: str) -> bool:
        return True if self.name == val or self.path == val or self.md5 == val else False

    
    def is_simple(self) -> bool:
        return self.path == self.name