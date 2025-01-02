from typing import Literal, Any
from pydantic import Field, BaseModel


class ExitStatus(BaseModel, extra="allow"):
    # @TODO: Is None actuall allowed?
    exit_status: Literal["*"] | int | None = Field(
        default=None,
        description="The exit status number that will cause this job to soft-fail",
    )


# NB: This may seem annoying (having to do `any(status == '*' for soft_fail in model.soft_fail)`)
#   however consider if we allowed `bool`. `if model.soft_fail` would be ambiguous (because a non-empty list is truthy)
# @TODO: Provide helper method for this
# class _SoftFailCanonicalizer(
#     Canonicalizer[LooseBoolT | list[ExitStatus] | None, list[ExitStatus]]
# ):
#     @classmethod
#     def canonicalize(
#         cls, value: LooseBoolT | list[ExitStatus] | None
#     ) -> list[ExitStatus]:
#         # @TODO: Does `_LooseBoolCanonicalizer` already fire?
#         if value == "true" or value is True:
#             return [ExitStatus(exit_status="*")]
#         if value is None or value == "false" or value is False:
#             return []
#         return value


# @TODO: RHS shouldn't be `Any`, but it kinda is upstream
# But there's a twist!
#   `env` at the pipeline level enforces RHS `str | int | bool` (with bools coerced to `true` ro `False`)
#   `env` at the command level just silently ignores non-int/str/bool
# (what gives?!)
# @TODO: Coerce RHS from strings? E.g. `"1"` -> `1` and `"true"` -> `True`
def env_from_json(value: dict[str, Any]) -> dict[str, str]:
    return {k: str(v) for k, v in value.items()}


def bool_from_json(value: Literal[True, False, "true", "false"]) -> bool:
    return value in (True, "true")


def list_str_from_json(value: str | list[str]) -> list[str]:
    return value if isinstance(value, list) else [value]
