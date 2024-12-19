from typing import dataclass_transform, Any, ClassVar
import dataclasses

from shimbboleth._model.field_alias import FieldAlias

# NB: This is just a heirarchical Model helper, with kw_only=True and slots=True.
#   (@TODO: Ideally we ensure none of the other nonsense is there? But also meh?)


@dataclass_transform(kw_only_default=True, field_specifiers=(dataclasses.field,))
class ModelMeta(type):
    __allow_extra_properties__: bool
    __field_aliases__: dict[str, FieldAlias]

    def __new__(mcls, name, bases, namespace, *, extra: bool | None = None):
        cls = super().__new__(
            mcls,
            name,
            bases,
            namespace,
        )
        # NB: Because you get a new type when adding `__slots__`,
        #   `dataclass` actualy returns a new type when using `slots=True`.
        #   That means this constructor will run again, but this time we
        #   already have the slotted dataclass.
        #   We can tell if it's a dataclass if it has the magic attribute.
        if "__dataclass_fields__" in cls.__dict__:
            return cls
        return dataclasses.dataclass(slots=True)(cls)

    def __init__(cls, name, bases, namespace, *, extra: bool | None = None):
        cls.__allow_extra_properties__ = bool(extra)

        if not hasattr(cls, "__field_aliases__"):
            cls.__field_aliases__ = {}
        cls.__field_aliases__ = cls.__field_aliases__.copy()
        for name, type in cls.__dict__.get("__annotations__", {}).items():
            if type is not ClassVar:
                continue
            class_attr = getattr(cls, name)
            if not isinstance(class_attr, FieldAlias):
                continue
            cls.__field_aliases__[name] = class_attr

    @property
    def model_json_schema(cls) -> dict[str, Any]:
        from shimbboleth._model.json_schema import JSONSchemaVisitor

        json_schema_visitor = JSONSchemaVisitor()
        json_schema_visitor.visit(cls)
        model_defs = json_schema_visitor.model_defs.copy()
        return {**model_defs.pop(cls.__name__), "$defs": model_defs}
