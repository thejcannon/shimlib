from functools import singledispatch
from typing import Any, TypeVar, cast, TYPE_CHECKING
from types import UnionType, GenericAlias
import re
import uuid
import dataclasses
import logging

from shimbboleth._model.model_meta import ModelMeta
from shimbboleth._model.model import Model
from shimbboleth._model._types import AnnotationType, LiteralType, GenericUnionType

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=Model)


LOG = logging.getLogger()


class ExtrasNotAllowedError(TypeError):
    pass


class NotAValidUUIDError(TypeError):
    pass


class NotAValidPatternError(TypeError):
    pass


class WrongTypeError(TypeError):
    def __init__(self, expected, data):
        super().__init__(f"Expected {expected}, got {type(data)}")


def _ensure_is(data, expected: type[T]) -> T:
    if type(data) is not expected:
        raise WrongTypeError(expected, data)
    return data


@singledispatch
def load(field_type, *, data):  # type: ignore
    if field_type is bool:
        return load_bool(data)
    if field_type is int:
        return load_int(data)
    if field_type is str:
        return load_str(data)
    # NB: type[None] from unions (e.g. `str | None`)
    if field_type is None or field_type is type(None):
        return load_none(data)
    if field_type is re.Pattern:
        return load_pattern(data)
    if field_type is uuid.UUID:
        return load_uuid(data)
    if field_type is Any:
        return data
    # NB: Dispatched manually, so we can avoid ciruclar definition with `Model.model_load`
    if isinstance(field_type, ModelMeta):
        return field_type.model_load(data)

    raise WrongTypeError(field_type, data)


@load.register
def load_generic_alias(field_type: GenericAlias, *, data: Any):
    container_t = field_type.__origin__
    if container_t is list:
        return load_list(data, field_type=cast(type[list], field_type))
    if container_t is dict:
        return load_dict(data, field_type=cast(type[dict], field_type))


@load.register
def load_union_type(field_type: UnionType, *, data: Any):
    # @TODO: Do we want to store a breadcrumb on the type here?
    for t in field_type.__args__:
        try:
            return load(t, data=data)
        except TypeError:
            pass
    raise WrongTypeError(field_type, data)


@load.register
def _load_generic_union_type(field_type: GenericUnionType, *, data: Any):
    return load_union_type(field_type, data=data)


@load.register
def load_literal(field_type: LiteralType, *, data: Any):
    # @TODO: This is duplicated in `validation` (for annotated literals)
    for possibility in field_type.__args__:
        # NB: compare bool/int by identity (since `bool` inherits from `int`)
        if data is possibility:
            return data
        if isinstance(possibility, str) and isinstance(data, str):
            if data == possibility:
                return data
    raise WrongTypeError(field_type, data)


@load.register
def load_annotation(field_type: AnnotationType, *, data: Any):
    baseType = field_type.__origin__
    return load(baseType, data=data)


def load_bool(data: Any) -> bool:
    return _ensure_is(data, bool)


def load_str(data: Any) -> str:
    return _ensure_is(data, str)


def load_int(data: Any) -> int:
    return _ensure_is(data, int)


def load_none(data: Any) -> None:
    return _ensure_is(data, type(None))


def load_list(data: Any, *, field_type: type[list[T]]) -> list[T]:
    data = _ensure_is(data, list)
    (argT,) = field_type.__args__
    return [load(argT, data=item) for item in data]


def load_dict(data: Any, *, field_type: type[dict]) -> dict:
    data = _ensure_is(data, dict)
    keyT, valueT = field_type.__args__
    return {
        load(keyT, data=key): load(valueT, data=value) for key, value in data.items()
    }


def load_pattern(data: Any) -> re.Pattern:
    data = _ensure_is(data, str)
    try:
        return re.compile(data)
    except re.error:
        raise NotAValidPatternError(data)


def load_uuid(data: Any) -> uuid.UUID:
    data = _ensure_is(data, str)
    try:
        return uuid.UUID(data)
    except ValueError:
        raise NotAValidUUIDError(data)


class _LoadModelHelper:
    @staticmethod
    def handle_field_aliases(model_type: type[Model], data: dict[str, Any]) -> dict:
        data = data
        for field_alias_name, field_alias in model_type.__field_aliases__.items():
            if field_alias_name in data:
                if data is data:
                    data = data.copy()

                value = data.pop(field_alias_name)
                if (
                    field_alias.json_mode == "prepend"
                    or data.get(field_alias.alias_of) is None
                ):
                    data[field_alias.alias_of] = value

        return data

    @staticmethod
    def rename_json_aliases(model_type: type[Model], data: dict[str, Any]):
        for field in dataclasses.fields(model_type):
            if not field.init:
                continue
            json_alias = field.metadata.get("json_alias")
            if json_alias and json_alias in data:
                data[field.name] = data.pop(json_alias)

    @staticmethod
    def get_extras(model_type: type[Model], data: dict[str, Any]) -> dict[str, Any]:
        extras = {}
        for field in frozenset(data.keys()):
            if field not in model_type.__json_fieldnames__:
                extras[field] = data.pop(field)

        if extras and not model_type.__allow_extra_properties__:
            # @TODO: Include more info in error
            raise ExtrasNotAllowedError(extras)

        return extras

    @staticmethod
    def load_field(field: dataclasses.Field, data: dict[str, Any]):
        json_loader = field.metadata.get("json_loader", None)
        expected_type = (
            json_loader.__annotations__["value"] if json_loader else field.type
        )

        value = load(expected_type, data=data[field.name])

        if json_loader:
            value = json_loader(value)

        return value


def load_model(model_type: type[ModelT], data: Any) -> ModelT:
    data = load(dict[str, Any], data=data)
    data = _LoadModelHelper.handle_field_aliases(model_type, data)

    extras = _LoadModelHelper.get_extras(model_type, data)
    _LoadModelHelper.rename_json_aliases(model_type, data)

    init_kwargs = {
        field.name: _LoadModelHelper.load_field(field, data)
        for field in dataclasses.fields(model_type)
        if field.name in data
    }

    instance = model_type(**init_kwargs)
    instance._extra = extras
    return instance


if TYPE_CHECKING:

    def load(field_type: type[T], *, data: Any) -> T: ...
