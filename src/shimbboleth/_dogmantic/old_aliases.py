from dataclasses import dataclass
from typing import Any, Literal
from pydantic import BaseModel, AliasChoices, model_validator
from pydantic.fields import FieldInfo, Field
import pydantic_core.core_schema
import pydantic.json_schema


@dataclass
class FieldAlias:
    alias_of: str
    mode: Literal["prepend", "append"] = "append"
    description: str | None = None
    deprecated: bool = False

    # @TODO: add support for "use only one of X or Y or Z supported"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.alias_of)

    def __set__(self, obj, value):
        return setattr(obj, self.alias_of, value)


class OrderedAliasChoices(AliasChoices):
    choices: list[str]
    fieldname: str

    def __init__(self, *choices: str, fieldname: str | None = None) -> None:
        self.choices = list(choices)
        self.fieldname = fieldname or choices[0]

    def convert_to_aliases(self) -> list[list[str]]:
        return [[self.fieldname]] + [
            [alias] for alias in self.choices if alias != self.fieldname
        ]


class FieldAliasSupport(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def _field_aliases_validator(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return

        data = data.copy()
        for field_name, field_info in cls.model_fields.items():
            validation_alias = field_info.validation_alias
            if not isinstance(validation_alias, OrderedAliasChoices):
                continue

            if not any(alias in data for alias in validation_alias.choices):
                continue

            choice0 = validation_alias.choices[0]
            for alias in validation_alias.choices[1:]:
                if (
                    data.get(alias, None) is not None
                    and data.get(choice0, None) is None
                ):
                    data[choice0] = data[alias]
                data.pop(alias, None)

        return data

    def __init_subclass__(cls, **kwargs):
        aliased_fieldnames = {
            obj.alias_of
            for name, obj in cls.__dict__.items()
            if isinstance(obj, FieldAlias)
        }

        for name, obj in cls.__dict__.items():
            if isinstance(obj, FieldAlias):
                field_name = obj.alias_of
                field_info = cls.__dict__[obj.alias_of]
                mode = obj.mode

            elif name in aliased_fieldnames:
                if not isinstance(obj, FieldInfo):
                    # It's a default value
                    setattr(cls, name, Field(default=obj))
                    obj = getattr(cls, name)

                field_name = name
                field_info = obj
                mode = "append"
            else:
                continue

            validation_alias = field_info.validation_alias
            if validation_alias is None:
                field_info.validation_alias = OrderedAliasChoices(
                    name, fieldname=field_name
                )
            elif isinstance(validation_alias, OrderedAliasChoices):
                if mode == "prepend":
                    validation_alias.choices.insert(0, name)
                else:
                    validation_alias.choices.append(name)

        super().__init_subclass__()

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        core_schema,
        handler,
        /,
    ):
        json_schema = super().__get_pydantic_json_schema__(core_schema, handler)
        for name, subschema in json_schema["properties"].items():
            attr = getattr(cls, name, None)
            if isinstance(attr, FieldAlias):
                if attr.description:
                    subschema["description"] = attr.description
                if attr.deprecated:
                    subschema["deprecated"] = True
        return json_schema


class GenerateJsonSchemaWithAliases(pydantic.json_schema.GenerateJsonSchema):
    # NB: See https://github.com/pydantic/pydantic/issues/10957
    def model_fields_schema(self, schema):
        json_schema = super().model_fields_schema(schema)
        for fieldname, fieldschema in schema.get("fields", {}).items():
            validation_alias = fieldschema.get("validation_alias", None)
            if validation_alias and isinstance(validation_alias, list):
                for aliases in validation_alias:
                    if isinstance(aliases, list):
                        for alias in aliases:
                            if alias == fieldname:
                                continue

                            json_schema["properties"][alias] = {
                                # Can't use $ref, `pydantic.json_schema.GenerateJsonSchema` chokes
                                "$ref$": self.ref_template.format(
                                    model=f"{self.normalize_name(schema.get('model_name', ''))}/properties/{fieldname}"
                                ),
                            }
        return json_schema

    def generate(
        self,
        schema: pydantic_core.core_schema.CoreSchema,
        mode: pydantic.json_schema.JsonSchemaMode = "validation",
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = super().generate(schema, mode)

        def replace_dollar_ref_dollar(obj):
            if isinstance(obj, dict) and "$ref$" in obj:
                obj["$ref"] = obj.pop("$ref$")
            nested = (
                obj.values()
                if isinstance(obj, dict)
                else obj
                if isinstance(obj, list)
                else ()
            )
            for val in nested:
                replace_dollar_ref_dollar(val)

        replace_dollar_ref_dollar(json_schema)
        return json_schema
