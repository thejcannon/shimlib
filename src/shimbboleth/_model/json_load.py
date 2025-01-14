from functools import singledispatch
from typing import Any, TypeVar, TYPE_CHECKING
from types import UnionType, GenericAlias
import re
import uuid
import dataclasses
import logging

from shimbboleth._model.model_meta import ModelMeta
from shimbboleth._model.model import Model
from shimbboleth._model._types import AnnotationType, LiteralType, GenericUnionType
from shimbboleth._model.validation import InvalidValueError

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
    def __init__(self, model_type: type[Model], extras: dict[str, Any]):
        super().__init__(
            f"Extra properties not allowed for `{model_type.__name__}`: {extras}"
        )


class NotAValidUUIDError(JSONLoadError):
    pass


class NotAValidPatternError(JSONLoadError):
    pass


class MissingFieldsError(TypeError):
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
        return data
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

        if rawtype in typemap:
            # @TODO: Improve message
            raise TypeError(f"Overlapping types in Union: {unionT}")

        typemap[rawtype] = argT

    return typemap


@load.register
def load_union_type(field_type: UnionType, *, data: Any):
    # @TODO: make this a lookup table (and also disallow overlap (must use loader))
    #   (overlap would include dict+Model, or Model+Model)
    # @TODO: (and then) Move this implicit assertion to model declaration time

    typemap = _get_union_typemap(field_type)
    try:
        return load(typemap[type(data)], data=data)
    except KeyError:
        breakpoint()
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
        with JSONLoadError.context(f"[{index}]"):
            ret.append(load(argT, data=item))
    return ret


def load_dict(data: Any, *, field_type: GenericAlias) -> dict:
    data = _ensure_is(data, dict)
    keyT, valueT = field_type.__args__
    return {
        # @TODO: Mention key vs value in error
        load(keyT, data=key): load(valueT, data=value)
        for key, value in data.items()
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
        for data_key in frozenset(data.keys()):
            if data_key not in model_type.__json_fieldnames__:
                extras[data_key] = data.pop(data_key)

        if extras and not model_type.__allow_extra_properties__:
            raise ExtrasNotAllowedError(model_type, extras)

        return extras

    @staticmethod
    def load_field(field: dataclasses.Field, data: dict[str, Any]):
        json_loader = field.metadata.get("json_loader", None)
        expected_type = (
            json_loader.__annotations__["value"] if json_loader else field.type
        )

        with JSONLoadError.context(field.name):
            value = load(expected_type, data=data[field.name])
            if json_loader:
                value = json_loader(value)

        return value

    @staticmethod
    def check_required_fields(model_type: type[Model], data: dict[str, Any]):
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
    _LoadModelHelper.check_required_fields(model_type, init_kwargs)

    instance = model_type(**init_kwargs)
    instance._extra = extras
    return instance


if TYPE_CHECKING:

    def load(field_type: type[T], *, data: Any) -> T: ...
