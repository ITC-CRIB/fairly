from __future__ import annotations
from typing import List, Dict, Set

from . import Dataset
from ..metadata import Metadata
from ..file.local import LocalFile
from .remote import RemoteDataset
from ..client import Client
from typing import Callable

import fairly

import os
import os.path
from ruamel.yaml import YAML
import re
import csv
import datetime
import platform
from functools import cached_property
import zipfile
import hashlib

class LocalDataset(Dataset):
    """

    Attributes:
        _path (str): Path of the dataset
        _manifest_path (str): Path of the dataset manifest
        _includes (set): File inclusion rules
        _excludes (set): File exclusion rules
        _md5s (dict): MD5 hash cache of the files
        _yaml: YAML object

    Class Attributes:
        _regexps (dict): Regular expression cache of the file rules
    """

    _regexps: Dict = {}

    def __init__(self, path: str, auto_refresh: bool=True):
        """Initializes LocalDataset object.

        Args:
            path (str): Path of the dataset
            auto_refresh (bool): Set True to auto-refresh dataset information

        Raises:
            NotADirectoryError = Invalid dataset path
        """
        # Call parent method
        super().__init__(auto_refresh=auto_refresh)

        # Throw exception if invalid path
        if not os.path.isdir(path):
            raise NotADirectoryError

        # Set path
        self._path = path

        # Set manifest path
        self._manifest_path = os.path.join(path, "manifest.yaml")

        # Set file rules
        self._includes = None
        self._excludes = None

        # Load cached MD5 hashes
        self._load_md5s()

        self._yaml = YAML()
        self._yaml.allow_unicode = True
        self._yaml.encoding = "utf-8"


    def _get_manifest(self) -> Dict:
        """Retrieves dataset manifest

        Returns:
            Dataset manifest dictionary
        """
        # TODO: Add exception handling
        manifest = None
        if os.path.isfile(self._manifest_path):
            with open(self._manifest_path, "r", encoding="utf-8") as file:
                # REMARK: ruaml.yaml is used to preserve document structure
                # https://stackoverflow.com/questions/71024653/how-to-update-yaml-file-without-loss-of-comments-and-formatting-yaml-automatic
                manifest = self._yaml.load(file)

        if not manifest:
            manifest = {}

        defaults = {
            "metadata": {},
            "template": "",
            "files": {"includes": [], "excludes": []}
        }

        for key, val in defaults.items():
            if not manifest.get(key):
                manifest[key] = val

        return manifest


    @cached_property
    def path(self) -> str:
        """Path of the dataset"""
        return self._path


    @cached_property
    def template(self) -> str:
        """Metadata template of the dataset"""
        manifest = self._get_manifest()

        return manifest["template"]


    @property
    def remote_datasets(self) -> Dict:
        """Known remote datasets of the dataset."""
        manifest = self._get_manifest()

        datasets = {}
        for key, val in manifest.get("remotes", {}).items():
            client = fairly.client(key)
            datasets[key] = RemoteDataset(client, val)

        return datasets


    @property
    def includes(self) -> Set:
        """Inclusion rules of the dataset files"""
        if self._includes is None:
            manifest = self._get_manifest()
            self._includes = manifest["files"]["includes"]

        return self._includes


    @property
    def excludes(self) -> Set:
        """Exclusion rules of the dataset files"""
        if self._excludes is None:
            manifest = self._get_manifest()
            self._excludes = manifest["files"]["excludes"]

        return self._excludes


    def _get_metadata(self) -> Metadata:
        """Retrieves metadata of the dataset.

        Returns:
            Metadata of the dataset
        """
        manifest = self._get_manifest()

        return Metadata(**manifest["metadata"])


    def _set_manifest(self, manifest: Dict) -> None:
        """Stores the dataset manifest.

        Args:
            manifest (Dict): Dataset manifest

        Returns:
            None
        """
        if "metadata" not in manifest:
            manifest["metadata"] = {}

        if "files" not in manifest:
            manifest["files"] = {
                "includes": [],
                "excludes": [],
            }

        with open(self._manifest_path, "w", encoding="utf-8") as file:
            # TODO: Exception handling
            self._yaml.dump(manifest, file)


    def _save_metadata(self) -> None:
        """Stores dataset metadata."""
        manifest = self._get_manifest()
        manifest["metadata"].update(self.metadata.serialize())
        self._set_manifest(manifest)


    def _match_rule(self, name: str, rule: str) -> bool:
        """Tests if a file name matches the specified rule.

        The asterisk (*) and question mark (?) are used as wildcard characters.
        The asterisk matches any sequence of characters.
        The question mark matches any single character.
        Relative path and file name are handled separately to support path rules.
        Cached regular expressions are created for each rule internally.

        Examples rules:
        *            : All files
        *.pdf        : Files with the .pdf extension, e.g. file.pdf
        *.xls*       : Files with the extension starting with .xls, e.g.
                       file.xls, file.xlsx
        table_??.cvs : Files with the .csv extension that start with
                       table_ and end with two additional characters, e.g.
                       table_01.csv, table_a5.csv
        data/*.cvs   : Files with the .csv extension under the data
                       directory, e.g. data/table.csv, data/results.csv
        data/*/*.cvs : Files with the .csv extension under the sub-directories
                       of the data directory, e.g. data/set1/results.csv,
                       data/set2/results.csv

        Returns:
            True if file name matches the rule, False otherwise

        Raises:
            None

        """
        if not rule in self._regexps:
            regexps = []
            for part in os.path.normpath(rule).split(os.sep):
                if part:
                    pattern = re.escape(part).replace("\*", ".*").replace("\?", ".")
                    regexp = re.compile(f"^{pattern}$", re.IGNORECASE)
                else:
                    regexp = None
                regexps.append(regexp)
            self._regexps[rule] = regexps
        for i, part in enumerate(os.path.normpath(name).split(os.sep)):
            try:
                regexp = self._regexps[rule][i]
            except:
                regexp = None
            if part:
                if not regexp or not regexp.match(part):
                    return False
            elif regexp:
                return False
        return True


    def _get_files(self) -> List[LocalFile]:
        files = []
        excludes = self.excludes
        includes = self.includes
        dirs = [self.path]
        while dirs:
            dir = dirs.pop(0)
            for file in os.listdir(dir):
                fullpath = os.path.join(dir, file)
                if os.path.isdir(fullpath):
                    dirs.append(fullpath)
                else:
                    path = os.path.relpath(fullpath, self.path)

                    if fullpath == self._manifest_path:
                        continue

                    if includes:
                        matched = False
                        for rule in includes:
                            if isinstance(rule, str):
                                if self._match_rule(path, rule):
                                    matched = True
                                    break
                            else:
                                archive = list(rule.keys())[0]
                                for rule in list(rule.values())[0]:
                                    if self._match_rule(path, rule):
                                        matched = True
                                        break
                                if matched:
                                    break
                        if not matched:
                            continue
                    else:
                        continue

                    if excludes:
                        matched = False
                        for rule in excludes:
                            if self._match_rule(path, rule):
                                matched = True
                                break
                        if matched:
                            continue

                    size = None
                    md5 = None
                    if path in self._md5s:
                        date, size, md5 = self._md5s[path]
                        if not date or date != os.path.getmtime(fullpath) or size != os.path.getsize(fullpath):
                            size = None
                            md5 = None
                    file = LocalFile(
                        fullpath,
                        basepath = self.path,
                        md5 = md5
                    )
                    files.append(file)
        return files


    def _load_md5s(self) -> None:
        """Loads MD5 hashes stored in the dataset directory"""
        self._md5s = {}
        path = os.path.join(self.path, ".fairly_md5")
        try:
            with open(path, "r") as file:
                reader = csv.reader(file)
                for name, date, size, md5 in reader:
                    self._md5s[name] = (date, size, md5)
        except FileNotFoundError:
            pass


    def save_files(self, force: bool=False) -> None:
        """Stores dataset file list if exists.

        Args:
            force (bool): Set True to enforce save even if existing dataset is modified

        Returns:
            None

        Raises:
            Warning("Existing dataset is modified")
        """
        # REMARK: It can be better to check if file list is actually changed
        if self.is_modified and not force:
            raise Warning("Existing dataset is modified")

        manifest = self._get_manifest()
        manifest["files"] = {
            "includes": self.includes,
            "excludes": self.excludes,
        }
        self._set_manifest(manifest)

        self.get_files(refresh=True)


    def save(self) -> None:
        """Saves metadata and file inclusion/exclusion rules."""
        self.save_metadata()
        self.save_files()


    def get_archive_name(self) -> str:
        """Returns archive name to be used for the dataset."""
        # TODO: Support for user-defined or metadata-based (e.g. title) name
        return "dataset"


    def get_archive_method(self) -> str:
        """Returns archiving method to be used for the dataset."""
        # TODO: Support for user-defined method
        return "deflate"


    def upload(self, repository=None, notify: Callable=None, strategy: str="auto", force: bool=False) -> RemoteDataset:
        """Uploads dataset to the repository.

        Available upload strategies:
            - auto: Mirror if folders are supported, otherwise archive folders individually.
            - mirror: Upload files and folders as they are.
            - archive_all: Create a single archive file for all files and folders.
            - archive_folders: Create an individual archive file for each folder.

        Args:
            repository: Repository identifier or client. If not specified, template identifier is used.
            notify (Callable): Notification callback function.
            strategy (str): Folder upload strategy (default = "auto")
            force (bool): Set True to upload dataset even if a remote version exists (default = False)

        Returns:
            Remote dataset

        Raises:
            ValueError("Invalid repository"): If repository argument is invalid.
            ValueError("Invalid upload strategy"): If upload strategy is invalid.
            ValueError("Invalid archiving method"): If archiving method is invalid.
            ValueError("Invalid archive name"): If archive name is invalid.
            Warning("Remote dataset exists"): If remote dataset exists.
        """
        # Set repository if required
        if not repository:
            repository = self.template

        # Get client
        if isinstance(repository, str):
            client = fairly.client(repository)
        elif isinstance(repository, Client):
            client = repository
        else:
            raise ValueError("Invalid repository")

        # Prevent upload if a remote version exists and upload is not enforced
        if client.repository_id in self.remote_datasets and not force:
            # TODO: Check if remote dataset is valid, otherwise force upload
            raise Warning("Remote dataset exists")

        # Create dataset
        dataset = client.create_dataset(self.metadata)

        files = self.get_files(refresh=True)

        allow_folders = client.supports_folder()

        if not strategy or strategy == "auto":
            strategy = "mirror" if allow_folders else "archive_folders"

        uploads = []
        archives = {}

        for file in files.values():

            if strategy == "archive_all":
                archives[self.get_archive_name()] = list(files.values())
                break

            if file.is_simple:
                uploads.append(file)

            elif strategy == "mirror":
                if allow_folders:
                    uploads.append(file)
                else:
                    raise ValueError("Invalid upload strategy")

            elif strategy == "archive_folders":
                name = os.path.normpath(file.path).split(os.sep)[0]
                if name not in archives:
                    archives[name] = [file]
                else:
                    archives[name].append(file)

            else:
                raise ValueError("Invalid upload strategy")

        try:
            # Upload files
            for file in uploads:
                client.upload_file(dataset, file, notify)

            # Upload archives if required
            if archives:
                methods = {
                    "store": zipfile.ZIP_STORED,
                    "deflate": zipfile.ZIP_DEFLATED,
                    "bzip2": zipfile.ZIP_BZIP2,
                    "lzma": zipfile.ZIP_LZMA,
                }
                method = methods.get(self.get_archive_method())
                if not method:
                    raise ValueError("Invalid archiving method")

                info = {}
                for name, files in archives.items():

                    path = os.path.join(self.path, f"{name}.zip")
                    if os.path.exists(path):
                        raise ValueError("Invalid archive name")

                    token = ""
                    with zipfile.ZipFile(path, "w", method) as archive:
                        for file in files:
                            archive.write(file.fullpath, file.path)
                            token += file.md5
                    md5 = hashlib.md5(str.encode(token)).hexdigest()

                    file = LocalFile(path, self.path)
                    client.upload_file(dataset, file, notify)

                    info[name] = {"md5": file.md5, "content": md5}
                    os.remove(path)

                # Update manifest
                manifest = self._get_manifest()
                manifest["files"]["archives"] = info
                self._set_manifest(manifest)

        except:
            client.delete_dataset(dataset.id)
            raise

        # Add remote dataset id to the manifest if known repository
        if client.repository_id:
            self.set_remote_dataset(dataset)

        return dataset


    @property
    def size(self) -> int:
        """Total size of the dataset in bytes."""
        size = 0
        for file in self.files.values():
            size += file.size

        return size


    @cached_property
    def created(self) -> datetime.datetime:
        """Creation date and time of the dataset"""
        # REMARK: On Unix systems getctime() returns the time of most recent
        # metadata change, but not the creation.
        # https://stackoverflow.com/questions/237079/how-do-i-get-file-creation-and-modification-date-times
        # https://docs.python.org/3/library/os.html#os.stat_result
        if platform.system() == "Windows":
            timestamp = os.path.getctime(self._manifest_path)

        else:
            stat = os.stat(self._manifest_path)
            try:
                timestamp = stat.st_birthtime
            except AttributeError:
                timestamp = stat.st_mtime

        return datetime.datetime.fromtimestamp(timestamp)


    @property
    def modified(self) -> datetime.datetime:
        """Last modification date and time of the dataset"""
        timestamp = os.path.getmtime(self._manifest_path)

        return datetime.datetime.fromtimestamp(timestamp)


    def synchronize(self, source, notify: Callable=None) -> None:
        if not isinstance(source, Dataset):
            source = fairly.dataset(source)

        diff = source.diff_metadata(self)
        # TODO: Synchronize metadata
        print(diff)

        diff = source.diff_files(self)

        for file in diff.added.values():
            pass


    def reproduce(self) -> LocalDataset:
        """Reproduces an actual copy of the dataset."""
        return LocalDataset(self.path)


    def set_remote_dataset(self, dataset) -> None:
        if not isinstance(dataset, RemoteDataset):
            dataset = fairly.dataset(dataset)
            if not isinstance(dataset, RemoteDataset):
                raise ValueError("Invalid remote dataset")

        id = dataset.client.repository_id
        if not id:
            raise ValueError("No repository id")

        manifest = self._get_manifest()
        if "remotes" not in manifest:
            manifest["remotes"] = {}
        manifest["remotes"][id] = dataset.id
        self._set_manifest(manifest)


    def get_remote_dataset(self, remote=None) -> RemoteDataset:
        if isinstance(remote, RemoteDataset):
            return remote

        elif not remote and self.metadata.get("doi"):
            return fairly.dataset(self.metadata["doi"])

        else:
            remote_datasets = self.remote_datasets
            if remote in remote_datasets:
                return  remote_datasets[remote]

            elif remote_datasets:
                return list(remote_datasets.values())[0]

        return None


    def push(self, target=None, notify: Callable=None) -> RemoteDataset:
        """
        Pushes local changes to metadata and files the data repository to 
        update a remote dataset. Dataset must exits in data repository.

        Args:
            target: Target repository identifier or client. If not specified, 
            identifier in manifest is used.
            notify (Callable): Notification callback function.

        Returns:
            Remote dataset
        
        Raises:
            ValueError("No target dataset"): If target dataset is not specified.

        """

        remote = self.get_remote_dataset(target)
        if not remote:
            raise ValueError("No target dataset")

        diff = self.diff_metadata(remote)
        if diff:
            remote.set_metadata(**self.metadata)
            remote.save_metadata()

        diff = self.diff_files(remote)
        if diff:
            client = remote.client
            for file in diff.added.values():
                client.upload_file(remote, file, notify=notify)

            for file in diff.removed.values():
                client.delete_file(remote, file)

            for file, remote_file in diff.modified.values():
                client.delete_file(remote, remote_file)
                client.upload_file(remote, file)

            remote.get_files(refresh=True)

        return remote


    def pull(self, source=None, notify: Callable=None) -> None:
        """
        Pulls changes made to metadata and files from the data repository
        to update the local dataset. Dataset must exits in data repository.

        Args:
            source: Source repository identifier or client. If not specified, 
            identifier in manifest is used.
            notify (Callable): Notification callback function.
        
        Returns:
            Remote dataset

        Raises:
            ValueError("No source dataset"): If source dataset is not specified.
            
        """

        remote = self.get_remote_dataset(source)
        if not remote:
            raise ValueError("No source dataset")

        diff = remote.diff_metadata(self)
        if diff:
            self.set_metadata(**remote.metadata)
            self.save_metadata()

        diff = remote.diff_files(self)
        if diff:
            client = remote.client
            for file in diff.added.values():
                client.download_file(file, path=self.path, notify=notify)

            for file in diff.removed.values():
                os.remove(file.fullpath)

            for file, remote_file in diff.modified.values():
                os.remove(file.fullpath)
                client.download_file(remote_file, path=self.path, notify=notify)

            self.get_files(refresh=True)

        return remote