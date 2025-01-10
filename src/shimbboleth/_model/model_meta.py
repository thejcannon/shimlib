from typing import dataclass_transform, Any, ClassVar, TypeVar
from types import MappingProxyType
import dataclasses

from shimbboleth._model.field import field
from shimbboleth._model.field_alias import FieldAlias
from shimbboleth._model._validators import ValidationDescriptor, get_validators


T = TypeVar("T")


@dataclass_transform(kw_only_default=True, field_specifiers=(dataclasses.field, field))
class ModelMeta(type):
    __allow_extra_properties__: bool
    __field_aliases__: MappingProxyType[str, FieldAlias] = MappingProxyType({})
    __json_fieldnames__: frozenset[str]

    def __new__(mcls, name, bases, namespace, *, extra: bool | None = None):
        cls = super().__new__(
            mcls,
            name,
            bases,
            namespace,
        )

        # NB: Copy the classcell so `super()` works and doesn't cause `TypeError` issues.
        if classcell := namespace.get("__classcell__"):
            cls.__classcell__ = classcell  # type: ignore

        # NB: Because you get a new type when adding `__slots__`,
        #   `dataclass` actualy returns a new type when using `slots=True`.
        #   That means this constructor will run again, but this time we
        #   already have the slotted dataclass.
        #   We can tell if it's a dataclass if it has the magic attribute.
        if "__dataclass_fields__" in cls.__dict__:
            return cls
        return dataclasses.dataclass(slots=True, kw_only=True)(cls)

    def __init__(cls, name, bases, namespace, *, extra: bool | None = None):
        cls.__allow_extra_properties__ = bool(extra)

        cls.__field_aliases__ = MappingProxyType(
            {
                **cls.__field_aliases__,
                **{
                    name: getattr(cls, name)
                    for name, type in cls.__dict__.get("__annotations__", {}).items()
                    if type is ClassVar and isinstance(getattr(cls, name), FieldAlias)
                },
            }
        )

        cls.__json_fieldnames__ = frozenset(
            field.metadata.get("json_alias", field.name)
            for field in dataclasses.fields(cls)  # type: ignore
        )

        # Replace the fields with validators with descriptors which invoke the validators before setting
        for field_attr in dataclasses.fields(cls):  # type: ignore
            field_validators = tuple(get_validators(field_attr.type))
            if field_validators:
                setattr(
                    cls,
                    field_attr.name,
                    ValidationDescriptor(
                        getattr(cls, field_attr.name), field_validators
                    ),
                )

    @property
    def model_json_schema(cls) -> dict[str, Any]:
        from shimbboleth._model.json_schema import schema

        model_defs = {}
        schema(cls, model_defs=model_defs)
        return {**model_defs.pop(cls.__name__), "$defs": model_defs}

    def model_load(cls: T, data: Any) -> T:
        raise NotImplementedError
