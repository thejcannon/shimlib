

from typing import TYPE_CHECKING, Annotated
from pydantic.fields import FieldInfo

class Description(FieldInfo):
    def __init__(self, description: str):
        super().__init__(description=description)


class Examples(FieldInfo):
    def __init__(self, *examples):
        super().__init__(examples=list(examples))

class MatchesRegex(FieldInfo):
    def __init__(self, regex: str):
        super().__init__(pattern=regex)



class _FieldT:
    def __class_getitem__(cls, params):
        # @TODO: Only one of params should be ones defined above.
        # Also typecheck examples (as best as possible)
        return cls

if TYPE_CHECKING:
    FieldT = Annotated
else:
    FieldT = _FieldT
