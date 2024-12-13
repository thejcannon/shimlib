from typing import Callable, TypeAlias, Any, TypeVar, overload
import dataclasses

T = TypeVar("T")

# @TODO: `Any` is lame, but both Anys are data/instance
ConverterFuncT: TypeAlias = Callable[[str, Any, Any], dict[str, Any]]

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
    json_default: Any | None = None,
) -> T: ...


def field(
    *,
    json_converter: ConverterFuncT | None = None,
    json_default: Any | None = None,
    **field_kwargs,
) -> Any:
    # @TODO Validate json default matches python default post-conversion
    metadata = {}
    if json_converter:
        metadata["json_converter"] = json_converter
    if json_default:
        metadata["json_default"] = json_default
    return dataclasses.field(**field_kwargs, metadata=metadata)
