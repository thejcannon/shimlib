from typing import (
    TypeAlias,
    Sequence,
    MutableMapping,
    TYPE_CHECKING,
)

# @TODO: Use TypeAliasype for these, so we can see them in the visitors (notably json_schema)

if TYPE_CHECKING:
    JSON: TypeAlias = (
        MutableMapping[str, "JSON"] | Sequence["JSON"] | str | int | float | bool | None
    )
else:
    JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

JSONObject: TypeAlias = dict[str, "JSON"]
JSONArray: TypeAlias = list["JSON"]
