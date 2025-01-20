from functools import singledispatch
from typing import Any, TypeVar, TYPE_CHECKING
from types import UnionType, GenericAlias
import re
import uuid
import dataclasses
import logging

from shimbboleth.internal.clay.jsonT import JSONObject, JSON
from shimbboleth.internal.clay.model_meta import ModelMeta
from shimbboleth.internal.clay.model import Model
from shimbboleth.internal.clay._types import (
    AnnotationType,
    LiteralType,
    GenericUnionType,
)
from shimbboleth.internal.clay.validation import InvalidValueError

T = TypeVar("T")
ModelT = TypeVar("ModelT", bound=Model)


LOG = logging.getLogger()


class JSONLoadError(InvalidValueError, TypeError):
    pass


class WrongTypeError(JSONLoadError):
    def __init__(self, expected, data):
        super().__init__(
            f"Expected `{expected}`, got `{data!r}` of type `{type(data).__name__}`"
        )


class ExtrasNotAllowedError(JSONLoadError):
    def __init__(self, model_type: type[Model], extras: JSONObject):
        super().__init__(
            f"Extra properties not allowed for `{model_type.__name__}`: {extras}"
        )


class NotAValidUUIDError(JSONLoadError):
    def __init__(self, data):
        super().__init__(f"Expected a valid UUID, got `{data!r}`")


class NotAValidPatternError(JSONLoadError):
    def __init__(self, data):
        super().__init__(f"Expected a valid regex pattern, got `{data!r}`")


class MissingFieldsError(JSONLoadError):
    def __init__(self, model_name: str, *fieldnames: str):
        fieldnames = tuple(f"`{field}`" for field in fieldnames)
        super().__init__(
            f"`{model_name}` missing {len(fieldnames)} required fields: {', '.join(fieldnames)}"
        )


def _ensure_is(data, expected: type[T]) -> T:
    if type(data) is not expected:
        raise WrongTypeError(expected.__name__, data)
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
        # @TODO: Remove this
        return data
    # NB: This is a string because it's a recursively defined type
    if field_type == "JSON":
        return load(JSON, data=data)  # type: ignore
    # NB: Dispatched manually, so we can avoid ciruclar definition with `Model.model_load`
    if issubclass(field_type, Model):
        return field_type.model_load(data)

    raise WrongTypeError(field_type, data)


@load.register
def load_generic_alias(field_type: GenericAlias, *, data: Any):
    container_t = field_type.__origin__
    if container_t is list:
        return load_list(data, field_type=field_type)
    if container_t is dict:
        return load_dict(data, field_type=field_type)


def _get_union_typemap(unionT: UnionType):
    typemap = {}
    has_literal = False
    for argT in unionT.__args__:
        rawtype = argT
        if isinstance(rawtype, LiteralType):
            if has_literal:
                raise TypeError(f"Multiple literals in Union: {unionT}")
            has_literal = True
            literal_types = {type(val) for val in rawtype.__args__}
            if len(literal_types) > 1:
                raise TypeError(f"Literal args must all be the same type: {unionT}")
            rawtype = literal_types.pop()

        while hasattr(rawtype, "__origin__"):
            rawtype = rawtype.__origin__

        if isinstance(rawtype, ModelMeta):
            rawtype = dict
        elif rawtype is re.Pattern:
            rawtype = str
        elif rawtype is uuid.UUID:
            rawtype = str

        if rawtype in typemap:
            # @TODO: Improve message
            raise TypeError(f"Overlapping types in Union: {unionT}")

        typemap[rawtype] = argT

    return typemap


def _get_jsontype(field_type) -> type:
    if isinstance(field_type, LiteralType):
        literal_types = {type(val) for val in field_type.__args__}
        if len(literal_types) > 1:
            raise TypeError(f"Literal args must all be the same type: {field_type}")
        return literal_types.pop()

    rawtype = field_type
    while hasattr(rawtype, "__origin__"):
        rawtype = rawtype.__origin__

    if isinstance(rawtype, ModelMeta):
        return dict
    if rawtype is re.Pattern:
        return str
    if rawtype is uuid.UUID:
        return str

    return rawtype


@load.register
def load_union_type(field_type: UnionType, *, data: Any):
    # @TODO: Some kind of assertion this is valid/safe
    #   (E.g. assert no two args are the same JSON type)
    #   (and put it in `ModelMeta`?)

    for argT in field_type.__args__:
        expected_type = _get_jsontype(argT)
        # NB: Have to use `is` instead of `isinstance` because `bool` inherits from `int`
        if type(data) is expected_type:
            return load(argT, data=data)

    raise WrongTypeError(field_type, data)


@load.register
def _load_generic_union_type(field_type: GenericUnionType, *, data: Any):
    return load_union_type(field_type, data=data)


@load.register
def load_literal(field_type: LiteralType, *, data: Any):
    # @TODO: This is duplicated in `validation` (for annotated literals)
    #   (Excpet not anymore? Did I forget some code?)
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


def load_list(data: Any, *, field_type: GenericAlias) -> list[T]:
    data = _ensure_is(data, list)
    (argT,) = field_type.__args__
    ret = []
    for index, item in enumerate(data):
        with JSONLoadError.context(index=index):
            ret.append(load(argT, data=item))
    return ret


def load_dict(data: Any, *, field_type: GenericAlias) -> dict:
    data = _ensure_is(data, dict)
    keyT, valueT = field_type.__args__
    # @TODO: Context?
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
    def handle_field_aliases(model_type: type[Model], data: JSONObject) -> dict:
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
    def rename_json_aliases(model_type: type[Model], data: JSONObject):
        for field in dataclasses.fields(model_type):
            if not field.init:
                continue
            json_alias = field.metadata.get("json_alias")
            if json_alias and json_alias in data:
                data[field.name] = data.pop(json_alias)

    @staticmethod
    def get_extras(model_type: type[Model], data: JSONObject) -> JSONObject:
        extras = {}
        for data_key in frozenset(data.keys()):
            if data_key not in model_type.__json_fieldnames__:
                extras[data_key] = data.pop(data_key)

        if extras and not model_type.__allow_extra_properties__:
            raise ExtrasNotAllowedError(model_type, extras)

        return extras

    @staticmethod
    def load_field(field: dataclasses.Field, data: JSONObject):
        json_loader = field.metadata.get("json_loader", None)
        expected_type = (
            json_loader.__annotations__["value"] if json_loader else field.type
        )

        # @TODO: Use the alias in the context?
        with JSONLoadError.context(attr=field.name):
            value = load(expected_type, data=data[field.name])
            if json_loader:
                value = json_loader(value)

        return value

    @staticmethod
    def check_required_fields(model_type: type[Model], data: JSONObject):
        missing_fields = [
            field.name
            for field in dataclasses.fields(model_type)
            if field.init
            and field.name not in data
            and field.default is dataclasses.MISSING
            and field.default_factory is dataclasses.MISSING
        ]
        if missing_fields:
            raise MissingFieldsError(model_type.__name__, *missing_fields)


def load_model(model_type: type[ModelT], data: JSONObject) -> ModelT:
    data = load(JSONObject, data=data)
    data = _LoadModelHelper.handle_field_aliases(model_type, data)

    extras = _LoadModelHelper.get_extras(model_type, data)
    _LoadModelHelper.rename_json_aliases(model_type, data)

    init_kwargs = {
        field.name: _LoadModelHelper.load_field(field, data)
        for field in dataclasses.fields(model_type)
        if field.name in data
    }
    _LoadModelHelper.check_required_fields(model_type, init_kwargs)

    instance = model_type(**init_kwargs)
    instance._extra = extras
    return instance


if TYPE_CHECKING:

    def load(field_type: type[T], *, data: JSONObject) -> T: ...
