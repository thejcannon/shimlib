from types import UnionType
from typing import Any, Union
from shimbboleth._dogmantic.model import ModelMeta
from shimbboleth._dogmantic.field_types import (
    FieldT,
)


def validate(
    field_type: Union[
        type[bool],
        type[int],
        type[str],
        None,
        # @TODO: Enum?
        type[list[bool]],
        type[list[int]],
        type[list[str]],
        # @TODO: More list types
        type[dict[str, bool]],
        type[dict[str, int]],
        type[dict[str, str]],
        # @TODO: more dict types
        type[UnionType],
        type[FieldT],
        ModelMeta,
    ],
) -> dict[str, Any]:
    return {}
