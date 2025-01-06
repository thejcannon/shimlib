from typing import Literal, Any, Annotated

from shimbboleth._model import Model, NonEmptyList, Not


class ExitStatus(Model, extra=True):
    exit_status: Literal["*"] | int
    """The exit status number that will cause this job to soft-fail"""


def _rubystr_inner(value: Any) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, int):
        return str(value)
    elif isinstance(value, list):
        return "[" + ", ".join(_rubystr_inner(v) for v in value) + "]"
    elif isinstance(value, dict):
        return (
            "{"
            + ", ".join(f'"{k}"=>{_rubystr_inner(v)}' for k, v in value.items())
            + "}"
        )
    elif value is None:
        return "nil"
    else:
        raise ValueError(f"Unsupported type: {type(value)}")


def rubystr(value: Any) -> str:
    if isinstance(value, str):
        return value
    return _rubystr_inner(value)


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


def bool_from_json(value: Literal[True, False, "true", "false"]) -> bool:
    return value in (True, "true")


def skip_from_json(value: str | Literal[True, False, "true", "false"]) -> str | bool:
    if value in (True, False, "true", "false"):
        return bool_from_json(value)
    if value == "":
        return False
    return value


def list_str_from_json(value: str | list[str]) -> list[str]:
    return value if isinstance(value, list) else [value]


def soft_fail_from_json(
    value: Literal[True, False, "true", "false"] | list[ExitStatus],
) -> bool | NonEmptyList[Annotated[int, Not[Literal[0]]]]:
    if value in (True, "true"):
        return True
    elif value in (False, "false"):
        return False
    elif value == []:
        return False
    elif any(wrapped.exit_status == "*" for wrapped in value):
        return True
    return [wrapped.exit_status for wrapped in value]


def soft_fail_to_json(
    value: bool | NonEmptyList[Annotated[int, Not[Literal[0]]]],
) -> bool | list[dict[str, int]]:
    if isinstance(value, bool):
        return value
    return [{"exit_status": exit_status} for exit_status in value]
