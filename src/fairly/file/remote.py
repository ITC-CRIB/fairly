from . import File

import requests
import mimetypes
import os.path
from urllib.parse import urlparse


class RemoteFile(File):

    def __init__(self, url: str, id: str=None, path: str=None, size: int=None, type: str=None, md5: str=None):
        self._url = url
        self._id = id
        self._headers = None
        self._path = path
        self._name = os.path.basename(path) if path else None
        self._size = size
        self._type = type
        self._md5 = md5


    @property
    def url(self) -> str:
        return self._url


    @property
    def id(self) -> str:
        return self._id


    @property
    def headers(self) -> str:
        if self._headers is None:
            # TODO: Add error handling
            response = requests.head(self.url, allow_redirects=True)
            self._headers = response.headers
        return self._headers


    @property
    def name(self) -> str:
        if self._name is None:
            parts = urlparse(self.url)
            self._name = os.path.basename(parts.path)
        return self._name


    @property
    def size(self) -> int:
        if self._size is None:
            self._size = self.headers.get("content-length")
        return self._size


    @property
    def type(self) -> str:
        if self._type is None:
            self._type, _ = mimetypes.guess_type(self.url)
            if self._type is None:
                self._type = self.headers.get("content-type")
        return self._type


    @property
    def md5(self) -> int:
        if self._md5 is None:
            self._md5 = self.headers.get("content-md5")
        return self._md5


    def match(self, val: str) -> bool:
        return True if self.url == val or self.id == val else super().match(val)