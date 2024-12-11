from typing import TypeVar, Any, Generic, cast, Literal, Callable, ClassVar
from pydantic import GetCoreSchemaHandler
import pydantic_core
from dataclasses import dataclass

FuncT = TypeVar("FuncT", bound=Callable[[Any], Any])

@dataclass(frozen=True, slots=True)
class FromJSONConverter(Generic[FuncT]):
    """
    @TODO: Docstring
    """
    func: FuncT
    input_schema: pydantic_core.CoreSchema | None = None

    def _call_func(self, value, handler):
        return handler(self.func(value))

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        schema = handler(source_type)
        input_schema = self.input_schema or handler.generate_schema(
            self.func.__annotations__["value"]
        )
        if "choices" in input_schema:
            # Workaround https://github.com/pydantic/pydantic/issues/11033
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



def converter(fieldname: str):
    """
    @TODO: Docstring
    """
    def inner(func: FuncT) -> ClassVar:
        return FromJSONConverter(func)

    return inner
