""" LocalFile class module.

LocalFile class is used to perform operations on local files.

Usage example:

    >>> file = LocalFile("/path/to/local/file/filename.txt")
    >>> file.type
        application/text
    >>> file.size
        543
    >>> file.is_archive()
        False
"""
from . import File
from typing import Callable, List

import os
import os.path
import mimetypes
import hashlib
import zipfile
import tarfile


class LocalFile(File):
    """LocalFile class.

    Class Attributes:
        CHUNK_SIZE: Chunk size in bytes to calculate MD5 checksum (default = 65536)
    """
    CHUNK_SIZE = 2**16


    def __init__(self, fullpath: str, basepath: str = None, md5: str = None):
        """Initializes LocalFile object.

        Raises:
            ValueError("Invalid file path"): If fullpath is not a valid file path
        """
        if not os.path.isfile(fullpath):
            raise ValueError("Invalid file path")
        self._fullpath = fullpath
        self._path = os.path.relpath(
            fullpath, basepath) if basepath else fullpath
        self._name = os.path.basename(fullpath)
        self._size = os.path.getsize(fullpath)
        self._type = None
        self._md5 = md5


    @property
    def fullpath(self) -> str:
        """Full path of the file.

        Returns:
            Full path of the file (str).
        """
        return self._fullpath


    @property
    def type(self) -> str:
        """MIME type of the file.

        Returns:
            MIME type of the file (str).
        """
        if self._type is None:
            self._type, _ = mimetypes.guess_type(self.fullpath)
        return self._type


    @property
    def md5(self) -> str:
        """MD5 checksum of the file.

        Returns:
            MD5 checksum of the file (str).
        """
        if self._md5 is None:
            with open(self.fullpath, "rb") as file:
                md5 = hashlib.md5()
                while chunk := file.read(self.CHUNK_SIZE):
                    md5.update(chunk)
            self._md5 = md5.hexdigest()
        return self._md5


    @property
    def is_archive(self) -> bool:
        """Checks if file is an archive file.

        Returns:
            True if file is an archive file, False otherwise.
        """
        if zipfile.is_zipfile(self.fullpath):
            return True

        elif tarfile.is_tarfile(self.fullpath):
            return True

        else:
            return False


    def match(self, val: str) -> bool:
        """Checks if file matches the specified file identifier.

        Returns:
            True if file matches the specified file identifier, False otherwise.
        """
        return True if self.fullpath == val else super().match(val)


    def extract(self, path: str = None, notify: Callable = None) -> List:
        """Extracts archive file contents to a specified directory.

        Args:
            path: Path of the directory to extract to. Default is the
                current working directory.

            notify: Notification callback function. Three arguments are
                provided to the callback function:

                - file (LocalFile): File object of the extracted local file
                - current_size (int): Current total uncompressed size of
                    extracted files.
                - total_size (int): Total uncompressed size of the archive

        Raises:
          ValueError("Invalid path"): If path is not a directory path.
          ValueError("Invalid archive item {name}"): If archive item path is not valid.
          ValueError("Invalid archive file"): If file is not an archive file.

        Returns:
          List of names of extracted files (str).
        """
        # Raise exception if invalid path
        if path:
            if not os.path.isdir(path):
                raise ValueError("Invalid path")
        else:
            path = ""

        files = []

        # Check if ZIP archive
        if zipfile.is_zipfile(self.fullpath):

            # Open ZIP archive
            with zipfile.ZipFile(self.fullpath, "r") as archive:

                # Get list of items
                items = archive.infolist()

                # Calculate total size
                total_size = sum(item.file_size for item in items)

                # Extract items
                current_size = 0
                for item in items:

                    # REMARK: Absolute and non-canonical paths are corrected
                    # https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile.extract
                    # TODO: Add error handling
                    archive.extract(item, path)

                    files.append(item.filename)

                    # Call notify callback if required
                    if notify and not item.is_dir():

                        file = LocalFile(os.path.join(
                            path, item.filename), path)
                        current_size += file.size
                        notify(file, file.size, total_size, current_size)

        # Check if TAR archive
        elif tarfile.is_tarfile(self.fullpath):

            # Open TAR archive
            with tarfile.open(self.fullpath, "r") as archive:

                # Get list of items
                items = archive.getmembers()

                # Calculate total size
                total_size = sum(item.size for item in items)

                # Check validity of the archive content
                for item in items:

                    if os.path.normpath(item.name) != os.path.relpath(item.name):
                        raise ValueError(f"Invalid archive item {item.name}")

                # Extract items
                # REMARK: extractall() cannot be used as it sets owner attributes
                attrs = []

                current_size = 0
                for item in items:

                    itempath = os.path.join(path, item.name)
                    attrs.append(
                        {"path": itempath, "mode": item.mode, "time": item.mtime})

                    if item.isdir():
                        item.mode = 0o700

                    # TODO: Add error handling
                    archive.extract(item, path, set_attrs=False)

                    files.append(item.name)

                    # Call notify callback if required
                    if notify and item.isfile():
                        file = LocalFile(itempath, path)
                        current_size += file.size
                        notify(file, file.size, total_size, current_size)

                # Set file mode and modification times
                # REMARK: Reverse sorting is required to handle directories correctly
                attrs.sort(key=lambda item: item["path"], reverse=True)

                for item in attrs:
                    try:
                        os.chmod(item["path"], item["mode"])
                        os.utime(item["path"], (item["time"], item["time"]))
                    except:
                        pass

        else:
            raise ValueError("Invalid archive file")

        return files
