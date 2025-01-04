from typing import Any, Self, TypeVar, Callable
import copy
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
    def _json_converter_(field) -> Callable[[T], T]:
        assert isinstance(field, dataclasses.Field), "Did you forget to = field(...)?"
        assert (
            "json_converter" not in field.metadata
        ), f"Only one converter per field. Already: {field.metadata['json_converter']}"

        def decorator(func: T) -> T:
            # NB: `metadata` is immutable, so copy/reassign
            field.metadata = type(field.metadata)(
                field.metadata | {"json_converter": func}
            )
            return func

        return decorator

    @classmethod
    def model_load(cls: type[Self], value: dict[str, Any]) -> Self:
        return JSONLoadVisitor().visit(cls, obj=value)

    def model_dump(self) -> dict[str, Any]:
        ret = {}
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value == field.default or (
                field.default_factory is not dataclasses.MISSING
                and value == field.default_factory()
            ):
                continue

            if isinstance(value, dict):
                ret[field.name] = {
                    k: v.model_dump() if isinstance(v, Model) else copy.deepcopy(v)
                    for k, v in value.items()
                }
            elif isinstance(value, list):
                ret[field.name] = [
                    v.model_dump() if isinstance(v, Model) else copy.deepcopy(v)
                    for v in value
                ]
            elif isinstance(value, Model):
                ret[field.name] = value.model_dump()
            else:
                ret[field.name] = copy.deepcopy(value)
        return ret
