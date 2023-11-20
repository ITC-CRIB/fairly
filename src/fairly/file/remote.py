"""RemoteFile class module.

RemoteFile class is used to perform operations on remote files.
"""
from typing import Dict

from . import File

import requests
import mimetypes
import os.path
from urllib.parse import urlparse
import logging


class RemoteFile(File):
    """RemoteFile class.

    Attributes:
        _url (str): URL address of the remote file.
        _id (str): Identifier of the remote file.
        _headers (Dict): HTTP headers of the remote file.
    """

    def __init__(self, url: str, id: str=None, path: str=None, size: int=None, type: str=None, md5: str=None):
        """Initializes RemoteFile object.

        Args:
            url (str): URL address of the remote file.
            id (str): Identifier of the remote file (optional).
            path (str): Path of the remote file (optional).
            size (int): Size of the remote file in bytes (optional).
            type (str): Content type of the remote file (optional).
            md5 (str): MD5 checksum of the remote file (optional).
        """
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
        """URL address of the remote file."""
        return self._url


    @property
    def id(self) -> str:
        """Identifier of the remote file."""
        return self._id


    @property
    def headers(self) -> Dict:
        """HTTP headers of the remote file."""
        if self._headers is None:
            logging.info("Fetching HTTP headers from %s.", self.url)
            # TODO: Add error handling
            response = requests.head(self.url, allow_redirects=True)
            response.raise_for_status()
            logging.debug("Headers %s", response.headers)
            self._headers = response.headers

        return self._headers


    @property
    def name(self) -> str:
        """Name of the remote file."""
        if self._name is None:
            parts = urlparse(self.url)
            self._name = os.path.basename(parts.path)

        return self._name


    @property
    def size(self) -> int:
        """Size of the remote file in bytes.

        Content-Length header is used to get the size.
        It is only calculated once and cached for subsequent calls.
        """
        if self._size is None:
            self._size = self.headers.get("content-length")

        return self._size


    @property
    def type(self) -> str:
        """Content type of the remote file.

        Content type is guessed by using the URL address. If it fails, then
        Content-Type header is used to get the content type.
        It is only calculated once and cached for subsequent calls.
        """
        if self._type is None:
            self._type, _ = mimetypes.guess_type(self.url)
            if self._type is None:
                self._type = self.headers.get("content-type")

        return self._type


    @property
    def md5(self) -> str:
        """MD5 checksum of the remote file.

        Content-MD5 header is used to get the MD5 checksum.
        It is only calculated once and cached for subsequent calls.
        """
        if self._md5 is None:
            self._md5 = self.headers.get("content-md5")

        return self._md5


    def match(self, val: str) -> bool:
        """Checks if remote file matches the specified file identifier.

        File URL address and id are compared with the specified identifier in
        addition to the properties checked by File.match().

        Args:
            val (str): File identifier.

        Returns:
            True if file matches the specified file identifier, False otherwise.
        """
        return True if self.url == val or self.id == val else super().match(val)
