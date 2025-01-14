from typing import Any, Self, TypeVar, Callable
import dataclasses

from shimbboleth._model.model_meta import ModelMeta

T = TypeVar("T")


class _ModelBase:
    _extra: dict[str, Any]
    """
    If `extra` is `True`, then this contains any extra fields provided when loading.
    """


class Model(_ModelBase, metaclass=ModelMeta):
    @classmethod
    def _json_loader_(
        cls, field, *, json_schema_type: type | None = None
    ) -> Callable[[T], T]:
        # @TODO: TEMPORARY
        if isinstance(field, str):
            field = cls.__dataclass_fields__[field]

        # @TODO: Assert funcname?
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

        decorator.json_schema_type = json_schema_type  # type: ignore
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

    # @TODO: NOTE: This is isn't necessarily a JSON loader (so need to check key types)
    # But the loader COULD reference JSON types and on loading enforce correctness (since
    #   JSON types are unambiguous)
    @classmethod
    def model_load(cls: type[Self], value: dict[str, Any]) -> Self:
        from shimbboleth._model.json_load import load_model

        return load_model(cls, value)

    def model_dump(self) -> dict[str, Any]:
        from shimbboleth._model.json_dump import dump_model

        return dump_model(self)

    def __setattr__(self, name: str, value: Any):
        return super().__setattr__(name, value)
