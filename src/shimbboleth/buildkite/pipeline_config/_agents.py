from shimbboleth.internal.clay.jsonT import JSONObject

from shimbboleth.buildkite.pipeline_config._types import rubystr


# @TODO: "list[str]" seems to just ignore non-strings? (on command)
# @TODO: BK stores things in "k=v" format. What if there's duplicate keys?
#   Oh God, I think they just pass those right along...
def agents_from_json(value: list[str] | JSONObject) -> dict[str, str]:
    if isinstance(value, list):
        # @TODO: ignore non-strings
        return dict(
            (elem.split("=", 1) if "=" in elem else (elem, "true")) for elem in value
        )
    return {k: rubystr(v) for k, v in value.items() if v is not None}
