from types import UnionType, GenericAlias
import re
import uuid
import dataclasses
from typing import Any
from shimbboleth._model.model import ModelMeta
from typing_extensions import TypeAliasType
from shimbboleth._model.validation import (
    MatchesRegex,
    NonEmpty,
    Ge,
    Le,
    Not,
)
from shimbboleth._model.field_alias import FieldAlias
from shimbboleth._model._visitor import Visitor


@dataclasses.dataclass(frozen=True, slots=True)
class JSONSchemaVisitor(Visitor[dict[str, Any]]):
    model_defs: dict[str, dict[str, Any]] = dataclasses.field(default_factory=dict)

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

    def visit_literal(self, objType: type) -> dict[str, Any]:
        return {"enum": list(objType.__args__)}

    def visit_pattern(self, objType: type[re.Pattern]) -> dict[str, Any]:
        return {"type": "string", "format": "regex"}

    def visit_uuid(self, objType: type[uuid.UUID]) -> dict[str, Any]:
        return {
            "type": "string",
            "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        }

    def _visit_annotation_type(self, annotation: Any) -> dict[str, Any]:
        if isinstance(annotation, MatchesRegex):
            return {"pattern": annotation.regex.pattern}
        elif annotation is NonEmpty:
            return {"minLength": 1}
        elif isinstance(annotation, Ge):
            return {"minimum": annotation.bound}
        elif isinstance(annotation, Le):
            return {"maximum": annotation.bound}
        elif isinstance(annotation, Not):
            return {"not": self._visit_annotation_type(annotation.inner)}
        else:
            raise TypeError(f"Unsupported annotation: {annotation}")

    def visit_annotated(self, objType: type) -> dict[str, Any]:
        ret = self.visit(objType.__origin__)
        for annotation in objType.__metadata__:
            ret.update(self._visit_annotation_type(annotation))
        return ret

    def visit_type_alias_type(self, objType: TypeAliasType) -> dict[str, Any]:
        if objType.__name__ not in self.model_defs:
            schema = self.visit(objType.__value__)
            self.model_defs[objType.__name__] = schema

        return {"$ref": f"#/$defs/{objType.__name__}"}

    def _get_field_type_schema(self, field: dataclasses.Field) -> dict[str, Any]:
        json_loader = field.metadata.get("json_loader", None)
        if json_loader:
            input_type = getattr(json_loader, "json_schema_type", json_loader.__annotations__["value"])
            output_type = json_loader.__annotations__["return"]
            assert (
                output_type == field.type
            ), (
                f"for {json_loader} {output_type=} {field.type=}"
            )
            return self.visit(input_type)
        return self.visit(field.type)

    def visit_model_field(self, field: dataclasses.Field) -> dict[str, Any]:
        field_schema = self._get_field_type_schema(field)
        if field.default is not dataclasses.MISSING:
            field_schema["default"] = field.default
        elif field.default_factory is not dataclasses.MISSING:
            field_schema["default"] = field.default_factory()
        return field_schema

    def visit_field_alias(
        self, field_alias: FieldAlias, *, model_name: str
    ) -> dict[str, Any]:
        return {"$ref": f"#/$defs/{model_name}/properties/{field_alias.alias_of}"}

    def visit_model(self, objType: ModelMeta) -> dict[str, Any]:
        model_name = objType.__name__
        if model_name not in self.model_defs:
            fields = tuple(field for field in dataclasses.fields(objType) if field.init)
            schema = {
                "type": "object",
                "properties": {
                    **{field.name: self.visit_model_field(field) for field in fields},
                    **{
                        name: self.visit_field_alias(field_alias, model_name=model_name)
                        for name, field_alias in objType.__field_aliases__.items()
                    },
                },
                "required": [
                    field.name
                    for field in fields
                    if (
                        field.default is dataclasses.MISSING
                        and field.default_factory is dataclasses.MISSING
                    )
                ],
                "additionalProperties": objType.__allow_extra_properties__,
            }
            self.model_defs[model_name] = schema

        return {"$ref": f"#/$defs/{model_name}"}
