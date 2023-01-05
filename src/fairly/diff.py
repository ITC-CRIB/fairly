"""Diff class module.

Diff class is used to keep track of dataset modifications.

Usage example:

    >>> diff = Diff()
    >>> diff.modify("name", "Johnny", "John")
    >>> diff.modified
        {"name": ("Johnny", "John")}
"""
from typing import Dict

class Diff:
    """
    Attributes:
        _added (Dict): Items added
        _modified (Dict): Items modified
        _removed (Dict): Items removed
    """

    def __init__(self):
        self._added = {}
        self._modified = {}
        self._removed = {}


    def __bool__(self):
        return bool(self._added) or bool(self._modified) or bool(self._removed)


    def __repr__(self):
        return "{{'added': {}, 'modified': {}, 'removed': {}}}".format(self.added, self.modified, self.removed)


    @property
    def added(self) -> Dict:
        """Returns a dictionary of added items."""
        return self._added


    @property
    def modified(self) -> Dict:
        """Returns a dictionary of modified items."""
        return self._modified


    @property
    def removed(self) -> Dict:
        """Returns a dictionary of removed items."""
        return self._removed


    def add(self, key, val) -> None:
        """Appends an item to the diff set as added.

        Args:
            key: Item key
            val: Item value
        """
        self._added[key] = val


    def modify(self, key, val, oldval) -> None:
        """Appends an item to the diff set as modified.

        Args:
            key: Item key
            val: Item value
            oldVal: Old value of the item
        """
        self._modified[key] = (val, oldval)


    def remove(self, key, val) -> None:
        """Appends an item to the diff set as removed.

        Args:
            key: Item key
            val: Item value
        """
        self._removed[key] = val
