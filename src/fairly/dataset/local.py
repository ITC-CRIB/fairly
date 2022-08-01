from typing import List, Dict, Set

from . import Dataset
from ..metadata import Metadata
from ..file.local import LocalFile

import os.path
import yaml
import re
import csv

class LocalDataset(Dataset):
    """

    Attributes:
      _path (str)          : Path of the dataset
      _manifest_path (str) : Path of the dataset manifest
      _manifest            : Dataset manifest
      _md5s (dict)         : Cached MD5 hashes of the files
    """

    _regexps: Dict = {}

    def __init__(self, path: str, manifest_file: str="manifest.yaml"):
        """

        Raises:
          NotADirectoryError: Invalid dataset path

        """
        # Call parent method
        super().__init__()

        # Throw exception if invalid path
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Invalid dataset path {path}")

        # Set path
        self._path = path

        # Set manifest path
        self._manifest_path = os.path.join(path, manifest_file)

        # Get manifest
        self._manifest = self._get_manifest()

        # Load cached MD5 hashes
        self._load_md5s()


    def _get_manifest(self) -> Dict:
        # TODO: Add exception handling
        manifest = None
        if os.path.isfile(self._manifest_path):
            with open(self._manifest_path, "r") as file:
                # REMARK: safe_load returns None if file is empty
                manifest = yaml.safe_load(file)
        if not manifest:
            manifest = {}
        files = manifest.get("files", {})
        return {
            "metadata": manifest.get("metadata", {}),
            "files": {
                "includes": set(files.get("includes", [])),
                "excludes": set(files.get("excludes", [])),
            },
        }


    @property
    def path(self) -> str:
        return self._path


    @property
    def includes(self) -> Set:
        return self._manifest["files"]["includes"]


    @property
    def excludes(self) -> Set:
        return self._manifest["files"]["excludes"]


    def _get_metadata(self) -> Metadata:
        metadata = self._manifest["metadata"]
        return Metadata(**metadata)


    def _set_manifest(self, section: str=None) -> None:
        manifest = self._get_manifest()
        if not section or section == "metadata":
            manifest["metadata"] = self._manifest["metadata"]
        if not section or section == "files":
            manifest["files"] = self._manifest["files"]
        with open(self._manifest_path, "w") as file:
            # TODO: Exception handling
            yaml.emitter.Emitter.process_tag = lambda self, *args, **kw: None
            yaml.dump(manifest, file, default_flow_style=False)


    def _set_metadata(self, metadata: Metadata) -> None:
        self._manifest["metadata"].update(metadata.serialize())
        self._set_manifest("metadata")


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
            for part in os.path.split(rule):
                if part:
                    pattern = re.escape(part).replace("\*", ".*").replace("\?", ".")
                    regexp = re.compile(f"^{pattern}$", re.IGNORECASE)
                else:
                    regexp = None
                regexps.append(regexp)
            self._regexps[rule] = regexps
        for i, part in enumerate(os.path.split(name)):
            regexp = self._regexps[rule][i]
            if part:
                if not regexp or not regexp.match(part):
                    return False
            elif regexp:
                return False
        return True


    def _get_files(self) -> List[LocalFile]:
        files = []
        dirs = [self.path]
        while dirs:
            dir = dirs.pop(0)
            for file in os.listdir(dir):
                fullpath = os.path.join(dir, file)
                if os.path.isdir(fullpath):
                    dirs.append(fullpath)
                else:
                    path = os.path.relpath(fullpath, self.path)
                    if self._manifest["files"]["includes"]:
                        matched = False
                        for rule in self._manifest["files"]["includes"]:
                            if self._match_rule(path, rule):
                                matched = True
                                break
                        if not matched:
                            continue
                    if self._manifest["files"]["excludes"]:
                        matched = False
                        for rule in self._manifest["files"]["excludes"]:
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
        self._md5s = {}
        path = os.path.join(self.path, ".fairly_md5")
        try:
            with open(path, "r") as file:
                reader = csv.reader(file)
                for name, date, size, md5 in reader:
                    self._md5s[name] = (date, size, md5)
        except FileNotFoundError:
            pass