from . import File
from typing import Callable, List

import os
import os.path
import mimetypes
import hashlib
import zipfile
import tarfile


class LocalFile(File):

    CHUNK_SIZE = 2**16

    def __init__(self, fullpath: str, basepath: str = None, md5: str = None):
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

    def is_archive(self) -> bool:
        if zipfile.is_zipfile(self.fullpath):
            return True

        elif tarfile.is_tarfile(self.fullpath):
            return True

        else:
            return False

    def extract(self, path: str = None, notify: Callable = None) -> List:
        """
        Extracts archive file contents to a specified directory

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
          ValueError: If invalid path.
          ValueError: If invalid archive file.

        Returns:
          List of extracted files.
        """
        # Raise exception if invalid path
        if path:
            if not os.path.isdir(path):
                raise ValueError(f"Invalid path: {path}")
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
                        raise ValueError(f"Invalid archive item: {item.name}")

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
