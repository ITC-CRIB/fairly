from . import File

import os.path
import mimetypes
import hashlib

class LocalFile(File):

    CHUNK_SIZE = 2**16


    def __init__(self, fullpath: str, basepath: str=None, md5: str=None):
        if not os.path.isfile(fullpath):
            raise ValueError("Invalid file path")
        self._fullpath = fullpath
        self._path = os.path.relpath(fullpath, basepath) if basepath else fullpath
        self._name = os.path.basename(fullpath)
        self._size = os.path.getsize(fullpath)
        self._type = None
        self._md5 = md5


    @property
    def fullpath(self) -> str:
        return self._fullpath


    @property
    def type(self) -> str:
        if self._type is None:
            self._type, _ = mimetypes.guess_type(self.fullpath)
        return self._type


    @property
    def md5(self) -> str:
        if self._md5 is None:
            with open(self.fullpath, "rb") as file:
                md5 = hashlib.md5()
                while chunk := file.read(self.CHUNK_SIZE):
                    md5.update(chunk)
            self._md5 = md5.hexdigest()
        return self._md5


    def match(self, val: str) -> bool:
        return True if self.fullpath == val else super().match(val)