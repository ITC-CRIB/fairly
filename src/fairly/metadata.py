"""Metadata class module.

Metadata class is used to store metadata attributes in a standardized manner.

Usage example:

    >>> metadata = Metadata({"title": "Title", "DOI": "doi:xxx"})
    >>> metadata["authors"] = ["Doe, John"]

"""
from __future__ import annotations
from typing import Any, Dict
from collections.abc import MutableMapping

from .person import Person

import re

class Metadata(MutableMapping):
    """Metadata class.

    Attributes:
        _normalize (Callable): Attribute normalization method.
        _attrs (Dict): Metadata attributes.

    Class Attributes:
        REGEXP_DOI: Regular expression to validate DOI.
    """

    REGEXP_DOI = re.compile(r"^10.\d{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)


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


    def __setitem__(self, key, val):
        if bool(val) or isinstance(val, (bool, int, float)):
            self._attrs[key] = self._normalize(key, val)
        elif hasattr(self._attrs, key):
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
                if not re.match(Metadata.REGEXP_DOI, val):
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

        if out.get("authors"):
            out["authors"] = [author.serialize() for author in out["authors"]]

        return out


    def autocomplete(self, overwrite: bool=False, attrs: List=None, **kwargs) -> Dict:
        """Completes missing metadata attributes by using the available information.

        Args:
            overwrite: If True existing attributes are overwritten.
            attrs: List of attributes to be completed.
            **kwargs: Arguments for the specific autocomplete methods.

        Returns:
            A dictionary of attributes set by method.
        """
        updated = {}

        if self.get("authors") and (not attrs or "authors" in attrs):
            updated["authors"] = {}
            for key, val in enumerate(self["authors"]):
                result = val.autocomplete(overwrite=overwrite, **kwargs)
                if result:
                    updated["authors"][key] = result

        return updated