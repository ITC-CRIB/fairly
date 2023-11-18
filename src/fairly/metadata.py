"""Metadata class module.

Metadata class is used to store metadata attributes in a standardized manner.

Usage example:

    >>> metadata = Metadata({"title": "Title", "DOI": "doi:xxx"})
    >>> metadata["authors"] = ["Doe, John"]

"""
from __future__ import annotations
from typing import Any, Dict
from collections.abc import MutableMapping

from .person import Person, PersonList

import re
import copy
import sys
import ruamel.yaml

class Metadata(MutableMapping):
    """Metadata class.

    Attributes:
        _normalize (Callable): Attribute normalization method.
        _attrs (Dict): Metadata attributes.
        _basis (Dict): Basis of metadata attributes.

    Class Attributes:
        REGEXP_DOI: Regular expression to validate DOI.
    """

    REGEXP_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:a-z\d]+", re.IGNORECASE)


    def __init__(self, normalize: Callable=None, **kwargs):
        """Initializes Metadata object.

        The default normalization method `Metadata.normalize()` is not called
        if user-defined normalization method is provided.

        Args:
            normalize: User-defined normalization method.
            **kwargs: Metadata attributes.
        """
        self._normalize = normalize if normalize else Metadata.normalize
        self._attrs = {}
        for key, val in kwargs.items():
            if bool(val) or isinstance(val, (bool, int, float)):
                self._attrs[key] = self._normalize(key, val)

        self.rebase()


    def __setitem__(self, key, val):
        if bool(val) or isinstance(val, (bool, int, float)):
            self._attrs[key] = self._normalize(key, val)
        elif key in self._attrs:
            del self._attrs[key]


    def __getitem__(self, key):
        return self._attrs[key]


    def __delitem__(self, key):
        del self._attrs[key]


    def __iter__(self):
        return iter(self._attrs)


    def __len__(self):
        return len(self._attrs)


    def __str__(self):
        return str(self._attrs)


    def __repr__(self):
        return "Metadata({})".format(self._attrs)


    def rebase(self):
        self._basis = copy.deepcopy(self._attrs)


    @property
    def is_modified(self) -> bool:
        """Checks if metadata is modified.

        Returns:
            True is metadata is modified, False otherwise.
        """
        return self._attrs != self._basis


    @classmethod
    def normalize(cls, name: str, val) -> Any:
        """Normalizes metadata attribute value.

        Args:
            name: Attribute name.
            val: Attribute value.

        Returns:
            Normalized attribute value.

        Raises:
            ValueError: If invalid attribute value.
        """
        # Digital Object Identifier
        if name == "doi":
            if isinstance(val, str):
                val = val.lower()
                if val.startswith("doi:"):
                    val = val[4:]
                elif val.startswith("http://doi.org/"):
                    val = val[15:]
                elif val.startswith("https://doi.org/"):
                    val = val[16:]
                if not re.fullmatch(Metadata.REGEXP_DOI, val):
                    raise ValueError
            else:
                raise ValueError

        # Keywords
        elif name == "keywords":
            if isinstance(val, str):
                val = re.split(r"[,;\n]", val)
            try:
                val = [keyword.strip() for keyword in iter(val)]
            except TypeError:
                raise ValueError

        # Authors
        elif name == "authors":
            val = Person.get_persons(val)

        # Return normalized value
        return val


    def serialize(self) -> Dict:
        """Serializes metadata as a dictionary.

        Returns:
            Metadata dictionary.
        """
        out = self._attrs.copy()

        for key, val in out.items():

            if isinstance(val, Person):
                val = val.serialize()

            elif isinstance(val, PersonList):
                val = [person.serialize() for person in val]

            else:
                continue

            out[key] = val

        return out


    def autocomplete(self, overwrite: bool=False, attrs: List=None, **kwargs) -> Dict:
        """Completes missing metadata attributes by using the available information.

        Args:
            overwrite: Set True to overwrite existing attributes.
            attrs: List of attributes to be completed.
            **kwargs: Arguments for the specific autocomplete methods.

        Returns:
            A dictionary of attributes set by method.
        """
        updated = {}

        for key, val in self._attrs.items():

            if attrs and key not in attrs:
                continue

            if isinstance(val, Person):
                result = val.autocomplete(overwrite=overwrite, **kwargs)

            elif isinstance(val, PersonList):
                result = {}
                for index, person in enumerate(val):
                    res = person.autocomplete(overwrite=overwrite, **kwargs)
                    if res:
                        result[key] = res

            else:
                continue

            if result:
                updated[key] = result

        return updated


    def _remove_comments(self, d):
        """Removes comments from a YAML dictionary recursively."""

        # REMARK: https://stackoverflow.com/questions/60080325/how-to-delete-all-comments-in-ruamel-yaml
        if isinstance(d, dict):
            for k, v in d.items():
                self._remove_comments(k)
                self._remove_comments(v)

        elif isinstance(d, list):
            for elem in d:
                self._remove_comments(elem)

        try:
             # literal scalarstring might have comment associated with them
             attr = 'comment' if isinstance(d, ruamel.yaml.scalarstring.ScalarString) \
                      else ruamel.yaml.comments.Comment.attrib
             delattr(d, attr)
        except AttributeError:
            pass


    def print(self):
        """Pretty prints metadata."""

        yaml = ruamel.yaml.YAML()

        out = self.serialize()
        self._remove_comments(out)

        yaml.dump(out, sys.stdout)