from typing import Callable, TypeAlias, Any, TypeVar, overload
import dataclasses

T = TypeVar("T")

# @TODO: `Any` is lame, but its the data
ConverterFuncT: TypeAlias = Callable[[str, Any], dict[str, Any]]

# @TODO: Recursive JSON type Alias?


@overload
def field(
    *, json_converter: ConverterFuncT | None = None, json_default: Any | None = None
) -> Any: ...


@overload
def field(
    *,
    default: T,
    json_converter: ConverterFuncT | None = None,
    json_default: Any = dataclasses.MISSING,
) -> T: ...


def field(
    *,
    json_converter: ConverterFuncT | None = None,
    json_default: Any = dataclasses.MISSING,
    **field_kwargs,
) -> Any:
    # @TODO Validate json default matches python default post-conversion?
    metadata = {}
    if json_converter:
        metadata["json_converter"] = json_converter
    if json_default is not dataclasses.MISSING:
        metadata["json_default"] = json_default
    return dataclasses.field(**field_kwargs, metadata=metadata)
