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
        return self._added


    @property
    def modified(self) -> Dict:
        return self._modified


    @property
    def removed(self) -> Dict:
        return self._removed


    def add(self, key, val) -> None:
        self._added[key] = val


    def modify(self, key, val, oldval) -> None:
        self._modified[key] = (val, oldval)


    def remove(self, key, val) -> None:
        self._removed[key] = val
