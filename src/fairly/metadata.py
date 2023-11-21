"""Metadata class module.

Metadata class is used to store metadata attributes in a standardized manner.

Usage example:

    >>> metadata = Metadata({"title": "Title", "DOI": "doi:xxx"})
    >>> metadata["authors"] = ["Doe, John"]

"""
from __future__ import annotations
from typing import Any, Dict, List, Callable
from collections.abc import MutableMapping

from .person import Person, PersonList

import re
import copy
import sys
import ruamel.yaml


class Metadata(MutableMapping):
    """Metadata class.

    Attributes:
        _attrs (Dict): Metadata attributes.
        _basis (Dict): Basis of metadata attributes.
        _normalize (Callable): Attribute normalization method.
        _serialize (Callable): Attribute serialization method.

    Class Attributes:
        REGEXP_DOI: Regular expression to validate DOI.
    """

    REGEXP_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:a-z\d]+", re.IGNORECASE)


    def __init__(self, normalize: Callable=None, serialize: Callable=None, **kwargs):
        """Initializes Metadata object.

        The corresponding default methods are not called if user-defined
        attribute value normalization and serialization methods are provided.

        Args:
            normalize: Attribute value normalization method (optional).
            serialize: Attribute value serialization method (optional).
            **kwargs: Metadata attributes.
        """
        self._normalize = normalize if normalize else Metadata.normalize_value
        self._serialize = serialize if serialize else Metadata.serialize_value
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


    def rebase(self) -> None:
        """Updates the basis of the metadata attributes."""
        self._basis = copy.deepcopy(self._attrs)


    @property
    def is_modified(self) -> bool:
        """Checks if metadata is modified.

        Returns:
            True is metadata is modified, False otherwise.
        """
        return self._attrs != self._basis


    @classmethod
    def normalize_value(cls, key: str, val) -> Any:
        """Normalizes metadata attribute value.

        Supported attributes:
            - doi
            - keywords
            - authors

        Args:
            key (str): Attribute key.
            val: Attribute value.

        Returns:
            Normalized attribute value.

        Raises:
            ValueError: If invalid attribute value.
        """
        # Digital Object Identifier
        if key == "doi":
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
        elif key == "keywords":
            if isinstance(val, str):
                val = re.split(r"[,;\n]", val)
            try:
                val = [keyword.strip() for keyword in iter(val)]
            except TypeError:
                raise ValueError

        # Authors
        elif key == "authors":
            val = Person.get_persons(val)

        # Return normalized value
        return val


    @classmethod
    def serialize_value(cls, key: str, val) -> Any:
        """Serializes metadata attribute value.

        Supported attributes:
            - Any attribute with a data type of `Person`.
            - Any attribute with a data type of `PersonList`.

        Args:
            key (str): Attribute key.
            val: Attribute value.

        Returns:
            Serialized attribute value.
        """
        if isinstance(val, Person):
            return val.serialize()

        if isinstance(val, PersonList):
            return [person.serialize() for person in val]

        return copy.deepcopy(val)


    def serialize(self) -> Dict:
        """Serializes metadata as a dictionary.

        Returns:
            Metadata dictionary.
        """
        out = {}

        for key, val in self._attrs.items():
            out[key] = self._serialize(key, val)

        return out


    def autocomplete(self, overwrite: bool=False, attrs: List=None, **kwargs) -> Dict:
        """Completes missing metadata attributes by using the available information.

        Supported attributes:
            - Any attribute with a data type of `Person`.
            - Any attribute with a data type of `PersonList`.

        Args:
            overwrite (bool): Set True to overwrite existing attributes (default False).
            attrs (List): List of attributes to be completed (optional).
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


    def _remove_comments(self, var) -> None:
        """Removes comments from a YAML dictionary recursively.

        Args:
            var: YAML dictionary or a dictionary item, if called recursively.
        """
        # REMARK: Based on https://stackoverflow.com/questions/60080325/how-to-delete-all-comments-in-ruamel-yaml
        if isinstance(var, dict):
            for key, val in var.items():
                self._remove_comments(key)
                self._remove_comments(val)

        elif isinstance(var, list):
            for item in var:
                self._remove_comments(item)

        try:
             if isinstance(var, ruamel.yaml.scalarstring.ScalarString):
                attr = "comment"
             else:
                attr = ruamel.yaml.comments.Comment.attrib
             delattr(var, attr)

        except AttributeError:
            pass


    def print(self) -> None:
        """Pretty prints metadata.

        Serializes metadata and prints as YAML without comments.
        """
        yaml = ruamel.yaml.YAML()

        out = self.serialize()
        self._remove_comments(out)

        yaml.dump(out, sys.stdout)
