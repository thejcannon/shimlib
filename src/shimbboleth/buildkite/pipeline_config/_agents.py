from typing import Any

from ._types import rubystr


# @TODO: "Any" == JSON
# @TODO: "list[str]" seems to just ignore non-strings? (on command)
# @TODO: BK stores things in "k=v" format. What if there's duplicate keys?
#   Oh God, I think they just pass those right along...
#   (on command
def agents_from_json(value: dict[str, Any] | list[str]) -> dict[str, str]:
    if isinstance(value, list):
        # @TODO: ignore non-strings
        return dict(
            (elem.split("=", 1) if "=" in elem else (elem, "true")) for elem in value
        )
    return {k: rubystr(v) for k, v in value.items() if v is not None}
