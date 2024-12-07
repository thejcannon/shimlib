from typing import TypeVar, Any, Generic, cast, Literal
from pydantic import GetCoreSchemaHandler
import pydantic_core

JsonValueT = TypeVar("JsonValueT")
PythonValueT = TypeVar("PythonValueT")
T = TypeVar("T")


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
                handler.resolve_ref_schema(
                    cast(pydantic_core.CoreSchema, choice_schema)
                )
                for choice_schema in input_schema["choices"]
            ]

        metadata = {"pydantic_js_input_core_schema": input_schema}
        return pydantic_core.core_schema.no_info_wrap_validator_function(
            cls.canonicalize, schema=schema, metadata=metadata
        )


class LooseBoolValidator(Canonicalizer[Literal[True, False, "true", "false"], bool]):
    @classmethod
    def canonicalize(
        cls,
        value: Literal[True, False, "true", "false"],
        handler: pydantic_core.core_schema.ValidatorFunctionWrapHandler,
    ) -> bool:
        return True if value == "true" else False if value == "false" else value


class ListofStringCanonicalizer(Canonicalizer[str | list[str], list[str]]):
    @classmethod
    def canonicalize(
        cls,
        value: str | list[str],
        handler: pydantic_core.core_schema.ValidatorFunctionWrapHandler,
    ) -> list[str]:
        if isinstance(value, list):
            return value
        return [value]
