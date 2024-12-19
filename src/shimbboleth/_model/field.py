from typing import Callable, TypeAlias, Any, TypeVar, overload
import dataclasses

T = TypeVar("T")

# @TODO: `Any` is lame, but its the data
ConverterFuncT: TypeAlias = Callable[[str, Any], dict[str, Any]]

# @TODO: Recursive JSON type Alias?


# @TODO: add "json_alias" (with `with_` and `if`)
@overload
def field(
    *,
    json_converter: ConverterFuncT | None = None,
    json_default: Any = dataclasses.MISSING,
    json_alias: str | None = None,
) -> Any: ...


@overload
def field(
    *,
    default: T,
    json_converter: ConverterFuncT | None = None,
    json_default: Any = dataclasses.MISSING,
    json_alias: str | None = None,
) -> T: ...


def field(
    *,
    json_converter: ConverterFuncT | None = None,
    json_default: Any = dataclasses.MISSING,
    json_alias: str | None = None,
    **field_kwargs,
) -> Any:
    # @TODO Validate json default matches python default post-conversion?
    metadata = {}
    if json_converter:
        metadata["json_converter"] = json_converter
    if json_default is not dataclasses.MISSING:
        metadata["json_default"] = json_default
    if json_alias:
        metadata["json_alias"] = json_alias
    return dataclasses.field(**field_kwargs, metadata=metadata)
