from types import UnionType, GenericAlias
import dataclasses
from typing import Any
from shimbboleth._model.model import ModelMeta
from shimbboleth._model.field_types import (
    Description,
    Examples,
    MatchesRegex,
    NonEmpty,
)
from shimbboleth._model._visitor import Visitor


class _JsonSchemaVisitor(Visitor[dict[str, Any]]):
    def visit_bool_field(self, objType: type[bool]) -> dict[str, Any]:
        return {"type": "boolean"}

    def visit_int_field(self, objType: type[int]) -> dict[str, Any]:
        return {"type": "integer"}

    def visit_str_field(self, objType: type[str]) -> dict[str, Any]:
        return {"type": "string"}

    def visit_none_field(self, objType: None) -> dict[str, Any]:
        return {"type": "null"}

    def visit_list_field(self, objType: GenericAlias) -> dict[str, Any]:
        (argT,) = objType.__args__
        return {"type": "array", "items": generate(argT)}

    def visit_dict_field(self, objType: GenericAlias) -> dict[str, Any]:
        keyT, valueT = objType.__args__
        key_schema = generate(keyT)
        assert key_schema.pop("type") == "string"
        return {
            "type": "object",
            "additionalProperties": generate(valueT),
            **({"propertyNames": key_schema} if key_schema else {}),
        }

    def visit_union_type_field(self, objType: UnionType) -> dict[str, Any]:
        return {"oneOf": [generate(argT) for argT in objType.__args__]}

    def visit_annotated_field(self, objType: type) -> dict[str, Any]:
        ret = generate(objType.__origin__)
        for annotation in objType.__metadata__:
            if isinstance(annotation, Description):
                ret["description"] = annotation.description
            elif isinstance(annotation, Examples):
                # @TODO: Typecheck the examples
                ret["examples"] = annotation.examples
            elif isinstance(annotation, MatchesRegex):
                ret["pattern"] = annotation.regex
            elif annotation is NonEmpty:
                ret["minLength"] = 1
            else:
                raise TypeError(f"Unsupported annotation: {annotation}")
        return ret

    def visit_literal_field(self, objType: type) -> dict[str, Any]:
        return {"enum": list(objType.__args__)}

    def _get_field_type_schema(self, field: dataclasses.Field) -> dict[str, Any]:
        json_converter = field.metadata.get("json_converter", None)
        if json_converter:
            input_type = json_converter.__annotations__["value"]
            output_type = json_converter.__annotations__["return"]
            assert (
                output_type == field.type
            ), f"{output_type=} {field.type=}"  # @TODO: what about `Annotated`?
            return generate(input_type)
        return generate(field.type)

    def _get_field_schema(self, field: dataclasses.Field) -> dict[str, Any]:
        field_schema = self._get_field_type_schema(field)
        if "json_default" in field.metadata:
            field_schema["default"] = field.metadata["json_default"]
        elif field.default is not dataclasses.MISSING:
            field_schema["default"] = field.default
        return field_schema

    def visit_model_field(self, objType: ModelMeta) -> dict[str, Any]:
        fields = dataclasses.fields(objType)
        return {
            "type": "object",
            "properties": {
                field.name: self._get_field_schema(field) for field in fields
            },
            "required": [
                field.name for field in fields if field.default is dataclasses.MISSING
            ],
            "additionalProperties": objType.__allow_extra_properties__,
        }


def generate(objType: type) -> dict[str, Any]:
    return _JsonSchemaVisitor().visit(objType)
