from __future__ import annotations
from typing import Any, Dict, Union
from collections.abc import MutableMapping

from .person import Person

import re

class Metadata(MutableMapping):

    """

    Attributes:
        _normalize (Callable): Attribute normalization method
        _attrs (Dict): Metadata attributes

    Class Attributes:
        REGEXP_DOI: Regular expression to validate DOI
    """

    REGEXP_DOI = re.compile(r"^10.\d{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)


    def __init__(self, normalize: Callable=None, **kwargs):
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
        """Normalized metadata attribute value

        Args:
            name (str): Attribute name
            val: Attribute value

        Returns:
            Normalized attribute value
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
            val = Person.get_people(val)

        # Return normalized value
        return val


    def serialize(self) -> Dict:
        return self._attrs.copy()