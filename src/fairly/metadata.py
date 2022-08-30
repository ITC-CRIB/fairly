from __future__ import annotations
from typing import Any, Dict, Union
from collections.abc import MutableMapping

from .person import Person

import re

class Metadata(MutableMapping):


    REGEXP_DOI = re.compile(r"^10.\d{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)


    def __init__(self, **kwargs):
        attrs = {}
        for key, val in kwargs.items():
            if bool(val) or isinstance(val, (bool, int, float)):
                attrs[key] = self._get_value(key, val)
        self.__dict__.update(**attrs)


    def __setitem__(self, key, val):
        if bool(val) or isinstance(val, (bool, int, float)):
            self.__dict__[key] = self._get_value(key, val)
        elif hasattr(self.__dict__, key):
            del self.__dict__[key]


    def __getitem__(self, key):
        return self.__dict__[key]


    def __delitem__(self, key):
        del self.__dict__[key]


    def __iter__(self):
        return iter(self.__dict__)


    def __len__(self):
        return len(self.__dict__)


    def __str__(self):
        return str(self.__dict__)


    def __repr__(self):
        return "Metadata({})".format(self.__dict__)


    def _get_value(self, key: str, val) -> Any:
        """

        Returns:
          Standard attribute value

        Raises:
          ValueError

        """
        if key == "doi":
            val = val.lower()
            if val.startswith("doi:"):
                val = val[:4]
            if not re.match(self.REGEXP_DOI, val):
                raise ValueError

        elif key == "date":
            # TODO: Standardize date
            pass

        elif key == "keywords":
            if isinstance(val, str):
                val = re.split(r"[,;\n]", val)
            try:
                val = [keyword.strip() for keyword in iter(val)]
            except TypeError:
                raise ValueError

        elif key == "authors":
            val = Person.get_people(val)

        return val


    def serialize(self) -> Dict:
        """

        Returns:
          Dictionary of metadata attributes

        """
        return self.__dict__.copy()