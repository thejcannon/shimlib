from types import UnionType, GenericAlias
import dataclasses
from typing import Any
from shimbboleth._dogmantic.model import ModelMeta
from shimbboleth._dogmantic.field_types import (
    Description,
    Examples,
    MatchesRegex,
    NonEmpty,
)
from shimbboleth._dogmantic._visitor import Visitor


class _JsonSchemaVisitor(Visitor[dict[str, Any], None]):
    def visit_bool_field(
        self, obj: type[bool], *, context: None = None
    ) -> dict[str, Any]:
        return {"type": "boolean"}

    def visit_int_field(
        self, obj: type[int], *, context: None = None
    ) -> dict[str, Any]:
        return {"type": "integer"}

    def visit_str_field(
        self, obj: type[str], *, context: None = None
    ) -> dict[str, Any]:
        return {"type": "string"}

    def visit_none_field(self, obj: None, *, context: None = None) -> dict[str, Any]:
        return {"type": "null"}

    def visit_list_field(
        self, obj: GenericAlias, *, context: None = None
    ) -> dict[str, Any]:
        (argT,) = obj.__args__
        return {"type": "array", "items": generate(argT)}

    def visit_dict_field(
        self, obj: GenericAlias, *, context: None = None
    ) -> dict[str, Any]:
        keyT, valueT = obj.__args__
        key_schema = generate(keyT)
        assert key_schema.pop("type") == "string"
        return {
            "type": "object",
            "additionalProperties": generate(valueT),
            **({"propertyNames": key_schema} if key_schema else {}),
        }

    def visit_union_type_field(
        self, obj: type[UnionType], *, context: None = None
    ) -> dict[str, Any]:
        return {"oneOf": [generate(argT) for argT in obj.__args__]}

    def visit_annotated_field(
        self, obj: type, *, context: None = None
    ) -> dict[str, Any]:
        ret = generate(obj.__origin__)
        for annotation in obj.__metadata__:
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

    def visit_model_field(
        self, obj: ModelMeta, *, context: None = None
    ) -> dict[str, Any]:
        fields = dataclasses.fields(obj)
        return {
            "type": "object",
            "properties": {field.name: generate(field.type) for field in fields},
            "required": [
                field.name for field in fields if field.default is dataclasses.MISSING
            ],
            "additionalProperties": obj.__allow_extra_properties__,
        }


def generate(input) -> dict[str, Any]:
    return _JsonSchemaVisitor().visit(input)
