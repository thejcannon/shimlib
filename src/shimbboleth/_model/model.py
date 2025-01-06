from typing import Any, Self, TypeVar, Callable
import copy
import re
import dataclasses

from shimbboleth._model.validation import ValidationVisitor
from shimbboleth._model.model_meta import ModelMeta
from shimbboleth._model.json_load import JSONLoadVisitor

T = TypeVar("T")


class _ModelBase:
    _extra: dict[str, Any]
    """
    If `extra` is `True`, then this contains any extra fields provided when loading.
    """

    def __init__(self):
        self._extra = {}


class Model(_ModelBase, metaclass=ModelMeta):
    def __post_init__(self):
        # @TODO: Validation should also happen on property setting
        ValidationVisitor().visit(type(self), obj=self)

    @staticmethod
    def _json_loader_(field) -> Callable[[T], T]:
        # @TODO: Assert funcname
        assert isinstance(field, dataclasses.Field), "Did you forget to = field(...)?"
        assert (
            "json_loader" not in field.metadata
        ), f"Only one loader per field. Already: {field.metadata['json_loader']}"

        def decorator(func: T) -> T:
            # NB: `metadata` is immutable, so copy/reassign
            field.metadata = type(field.metadata)(
                field.metadata | {"json_loader": func}
            )
            return func

        return decorator

    @staticmethod
    def _json_dumper_(field) -> Callable[[T], T]:
        # @TODO: Assert funcname
        assert isinstance(field, dataclasses.Field), "Did you forget to = field(...)?"
        assert (
            "json_dumper" not in field.metadata
        ), f"Only one dumper per field. Already: {field.metadata['json_dumper']}"

        def decorator(func: T) -> T:
            # NB: `metadata` is immutable, so copy/reassign
            field.metadata = type(field.metadata)(
                field.metadata | {"json_dumper": func}
            )
            return func

        return decorator

    @classmethod
    def model_load(cls: type[Self], value: dict[str, Any]) -> Self:
        return JSONLoadVisitor().visit(cls, obj=value)

    def model_dump(self) -> dict[str, Any]:
        # @TODO: Put this in a visitor
        ret = {}
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value == field.default or (
                field.default_factory is not dataclasses.MISSING
                and value == field.default_factory()
            ):
                continue

            key = field.metadata.get("json_alias", field.name)
            if "json_dumper" in field.metadata:
                ret[key] = field.metadata["json_dumper"](value)
            elif isinstance(value, dict):
                ret[key] = {
                    k: v.model_dump() if isinstance(v, Model) else copy.deepcopy(v)
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                ret[key] = [
                    v.model_dump() if isinstance(v, Model) else copy.deepcopy(v)
                    for v in value
                ]
            elif isinstance(value, Model):
                ret[key] = value.model_dump()
            elif isinstance(value, re.Pattern):
                ret[key] = value.pattern
            else:
                ret[key] = copy.deepcopy(value)
        return ret
