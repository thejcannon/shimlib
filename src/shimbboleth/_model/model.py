from typing import Any, Self, TypeVar, Callable
import dataclasses

from shimbboleth._model.validation import ValidationVisitor
from shimbboleth._model.model_meta import ModelMeta
from shimbboleth._model.json_load import JSONLoadVisitor

T = TypeVar("T")


class Model(metaclass=ModelMeta):
    _extra: dict[str, Any] = dataclasses.field(
        default_factory=dict, init=False, repr=False, compare=False, hash=False
    )
    """
    If `extra` is `True`, then this contains any extra fields provided when loading.
    """

    def __post_init__(self):
        ValidationVisitor().visit(type(self), obj=self)

    @staticmethod
    def _json_converter_(field) -> Callable[[T], T]:
        assert "json_converter" not in field.metadata

        def decorator(func: T) -> T:
            field.metadata["json_converter"] = func
            return func

        return decorator

    @classmethod
    def model_load(cls: type[Self], value: dict[str, Any]) -> Self:
        return JSONLoadVisitor().visit(cls, obj=value)

    def model_dump(self) -> dict[str, Any]:
        # @TODO: asdict(self), but with aliases, and maybe some filtering
        raise NotImplementedError
