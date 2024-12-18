"""
Support for "aliases".

Features:
    - Allows fields to be loaded via (multiple) aliases
    - Supports alias heirarchies
    - Aliases appear in the JSON schema (as refs to the canonical field)
    - Aliases are descriptors shimming the fields they are aliases of
"""

import dataclasses
from typing import Literal


@dataclasses.dataclass
class FieldAlias:
    alias_of: str
    mode: Literal["prepend", "append"] = "append"
    deprecated: bool = False

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.alias_of)

    def __set__(self, obj, value):
        return setattr(obj, self.alias_of, value)
