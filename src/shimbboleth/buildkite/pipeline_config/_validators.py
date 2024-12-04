from typing import TypeVar, Any, Generic
from pydantic import GetCoreSchemaHandler
import pydantic_core

JsonValueT = TypeVar("JsonValueT")
PythonValueT = TypeVar("PythonValueT")


class Canonicalizer(Generic[JsonValueT, PythonValueT]):
    @classmethod
    def canonicalize(
        cls,
        value: JsonValueT,
        handler: pydantic_core.core_schema.ValidatorFunctionWrapHandler,
    ) -> PythonValueT:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> pydantic_core.CoreSchema:
        schema = handler(source_type)
        input_schema = handler.generate_schema(
            cls.canonicalize.__annotations__["value"]
        )
        if "choices" in input_schema:
            # Workaround https://github.com/pydantic/pydantic/issues/11033
            input_schema["choices"] = [
                handler.resolve_ref_schema(choice_schema)
                for choice_schema in input_schema["choices"]
            ]

        metadata = {"pydantic_js_input_core_schema": input_schema}
        return pydantic_core.core_schema.no_info_wrap_validator_function(
            cls.canonicalize, schema=schema, metadata=metadata
        )
