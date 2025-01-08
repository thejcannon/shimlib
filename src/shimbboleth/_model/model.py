from typing import Any, Self, TypeVar, Callable
import dataclasses

from shimbboleth._model.validation import ValidationVisitor
from shimbboleth._model.model_meta import ModelMeta

T = TypeVar("T")


class _ModelBase:
    _extra: dict[str, Any]
    """
    If `extra` is `True`, then this contains any extra fields provided when loading.
    """


class Model(_ModelBase, metaclass=ModelMeta):
    def __post_init__(self):
        # @TODO: Validation should also happen on property setting
        #   (which tells me that we should probably have a `__set__` method and use that)
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
        from shimbboleth._model.json_load import load_model

        return load_model(cls, value)

    def model_dump(self) -> dict[str, Any]:
        from shimbboleth._model.json_dump import dump_model

        return dump_model(self)

    def __setattr__(self, name: str, value: Any):
        return super().__setattr__(name, value)
