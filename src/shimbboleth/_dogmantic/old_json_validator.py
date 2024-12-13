# @TODO: Add `json_default` in (and maybe even check that it matches the Python default post-validation)
from typing import TypeVar, Any, Generic, cast, Callable, Annotated
import pydantic
import pydantic.fields
import pydantic_core
from dataclasses import dataclass

FuncT = TypeVar("FuncT", bound=Callable[[Any], Any])


@dataclass(frozen=True, slots=True)
class JsonValidator(Generic[FuncT]):
    """
    Validate the field coming from JSON using `func`.

    During JSON validation (including generating the JSON Schema), the
    input type is checked against the type of the `value` unary parameter
    of `func`.
    """

    # Ideally, just use WrapValidator, but it's somewhat borked:
    # https://github.com/pydantic/pydantic/issues/11033
    func: FuncT
    input_schema: pydantic_core.CoreSchema | None = None

    def _call_func(self, value, handler):
        return self.func(handler(value))

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: pydantic.GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        schema = handler(source_type)
        input_schema = self.input_schema or handler.generate_schema(
            self.func.__annotations__["value"]
        )
        if "choices" in input_schema:
            input_schema["choices"] = [
                handler.resolve_ref_schema(
                    cast(pydantic_core.CoreSchema, choice_schema)
                )
                for choice_schema in input_schema["choices"]
            ]

        metadata = {"pydantic_js_input_core_schema": input_schema}
        return pydantic_core.core_schema.no_info_wrap_validator_function(
            self._call_func, schema=schema, metadata=metadata
        )


class FieldInfo(pydantic.fields.FieldInfo):
    json_converter: Callable
    __slots__ = ["json_validator"]

    def __init__(self, *, json_validator, **kwargs) -> None:
        super().__init__(**kwargs)
        self.json_validator = json_validator


# @TODO: Copy some of these from pydantic?
def Field(*, json_validator, **kwargs) -> Any:
    return Field(json_validator=json_validator, **kwargs)


class SupportsConverterMixin:
    def __init_subclass__(cls, **kwargs):
        for key, value in cls.__dict__.items():
            if isinstance(value, FieldInfo):
                cls.__annotations__[key] = Annotated[
                    cls.__annotations__[key], JsonValidator(value.json_validator)
                ]
        return super().__init_subclass__(**kwargs)
