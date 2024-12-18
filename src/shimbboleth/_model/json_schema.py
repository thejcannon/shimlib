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
    def visit_bool(self, objType: type[bool]) -> dict[str, Any]:
        return {"type": "boolean"}

    def visit_int(self, objType: type[int]) -> dict[str, Any]:
        return {"type": "integer"}

    def visit_str(self, objType: type[str]) -> dict[str, Any]:
        return {"type": "string"}

    def visit_none(self, objType: None) -> dict[str, Any]:
        return {"type": "null"}

    def visit_list(self, objType: GenericAlias) -> dict[str, Any]:
        (argT,) = objType.__args__
        return {"type": "array", "items": self.visit(argT)}

    def visit_dict(self, objType: GenericAlias) -> dict[str, Any]:
        keyT, valueT = objType.__args__
        key_schema = self.visit(keyT)
        assert key_schema.pop("type") == "string"
        return {
            "type": "object",
            "additionalProperties": self.visit(valueT) if valueT is not Any else True,
            **({"propertyNames": key_schema} if key_schema else {}),
        }

    def visit_union_type(self, objType: UnionType) -> dict[str, Any]:
        return {"oneOf": [self.visit(argT) for argT in objType.__args__]}

    def visit_annotated(self, objType: type) -> dict[str, Any]:
        ret = self.visit(objType.__origin__)
        for annotation in objType.__metadata__:
            if isinstance(annotation, Description):
                ret["description"] = annotation.description
            elif isinstance(annotation, Examples):
                # @TODO: Typecheck the examples
                ret["examples"] = annotation.examples
            elif isinstance(annotation, MatchesRegex):
                ret["pattern"] = annotation.regex.pattern
            elif annotation is NonEmpty:
                ret["minLength"] = 1
            else:
                raise TypeError(f"Unsupported annotation: {annotation}")
        return ret

    def visit_literal(self, objType: type) -> dict[str, Any]:
        return {"enum": list(objType.__args__)}

    def _get_field_type_schema(self, field: dataclasses.Field) -> dict[str, Any]:
        json_converter = field.metadata.get("json_converter", None)
        if json_converter:
            input_type = json_converter.__annotations__["value"]
            output_type = json_converter.__annotations__["return"]
            assert (
                output_type == field.type
            ), f"{output_type=} {field.type=}"  # @TODO: what about `Annotated`?
            return self.visit(input_type)
        return self.visit(field.type)

    def visit_model_field(self, field: dataclasses.Field) -> dict[str, Any]:
        field_schema = self._get_field_type_schema(field)
        if "json_default" in field.metadata:
            field_schema["default"] = field.metadata["json_default"]
        elif field.default is not dataclasses.MISSING:
            field_schema["default"] = field.default
        return field_schema

    def visit_model(self, objType: ModelMeta) -> dict[str, Any]:
        fields = tuple(field for field in dataclasses.fields(objType) if field.init)
        return {
            "type": "object",
            "properties": {
                field.name: self.visit_model_field(field) for field in fields
            },
            "required": [
                field.name for field in fields if field.default is dataclasses.MISSING
            ],
            "additionalProperties": objType.__allow_extra_properties__,
        }


def generate(objType: type) -> dict[str, Any]:
    return _JsonSchemaVisitor().visit(objType)
